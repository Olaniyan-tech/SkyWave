from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from bookings.selectors import get_booking_by_reference
from payments.services.payment_service import initialize_payment, verify_payment
from payments.selectors import get_payment_by_reference, get_payment_by_booking, get_user_payments
from payments.serializers import PaymentInitializeSerializer, PaymentDetailSerializer
import hmac
import hashlib
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from payments.models import Payment
from payments.services.payment_service import handle_webhook_payment_update
import logging

logger = logging.getLogger(__name__)



class PaymentInitializeView(APIView):

    @method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True))
    def post(self, request):
        serializer = PaymentInitializeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        booking_reference = serializer.validated_data['booking_reference']
        
        booking = get_booking_by_reference(booking_reference, request.user)
        if not booking:
            return Response({
                "error": "Booking not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            authorization_url, payment_reference = initialize_payment(booking)
        except ValidationError as e:
            logger.warning(f"Payment initialization failed: {e}")
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "message": "Payment initialized. Please proceed to the authorization URL to complete the payment.",
            "authorization_url": authorization_url,
            "payment_reference": payment_reference,
            "amount": str(booking.total_amount),
            "currency": booking.currency
        }, status=status.HTTP_200_OK)


class PaymentVerifyView(APIView):

    @method_decorator(ratelimit(key='user', rate='30/m', method='GET', block=True))
    def get(self, request):
        reference = request.query_params.get("reference", "").strip()

        if not reference:
            return Response({
                "error": "Payment reference is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment_data = verify_payment(reference)
        except ValidationError as e:
            logger.warning(f"Payment verification failed for reference {reference}: {e}")
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
        
        paystack_status = payment_data.get("status")

        if paystack_status == "success":
            payment = get_payment_by_reference(reference)
            return Response({
                "message": "Payment verified successfully. Booking confirmed!",
                "payment_status": "PAID",
                "booking_status": "CONFIRMED",
                "payment": PaymentDetailSerializer(payment).data}, 
                status=status.HTTP_200_OK
            )

        elif paystack_status == "failed":
            return Response({
                "message": "Payment verification failed. Please try again.",
                "payment_status": "FAILED"}, 
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        else:
            return Response({
                "message": f"Payment status: {paystack_status}. Please check your payment and try again.", 
                "payment_status": paystack_status}, 
                status=status.HTTP_200_OK
            )


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    """
    POST /api/payments/webhook/

    Paystack calls this URL automatically after every payment event.
    No authentication needed — Paystack is not a logged-in user.
    Instead we verify the request using a signature check.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        paystack_signature = request.headers.get("x-paystack-signature")

        if not paystack_signature:
            return Response(
                {"error": "Missing signature"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        computed = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
            request.body,
            hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(computed, paystack_signature):
            logger.warning("Webhook received with invalid signature")
            return Response(
                {"error": "Invalid signature."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payload = request.data
            event = payload.get("event")
            reference = payload.get("data", {}).get("reference")

        except Exception:
            return Response(
                {"error": "Invalid payload."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reference:
            logger.warning("Webhook received with no reference")
            return Response({"message": "ok"}, status=status.HTTP_200_OK)

        try:
            payment = Payment.objects.select_related("booking", "booking__user").get(
                payment_reference=reference
            )

        except Payment.DoesNotExist:
            logger.warning("No payment found with reference %s", reference)
            return Response({"message": "ok"}, status=status.HTTP_200_OK)
        
        if event == "charge.success":
            handle_webhook_payment_update(payment, "PAID", payload.get("data", {}))
            logger.info("Webhook: Payment confirmed for booking %s", payment.booking.booking_reference)

        elif event == "charge.failed":
            handle_webhook_payment_update(payment, "FAILED", payload.get("data", {}))
            logger.info("Webhook: Payment failed for booking %s", payment.booking.booking_reference)

        # Always return 200 OK so Paystack doesn't keep retrying
        return Response({"message": "ok"}, status=status.HTTP_200_OK)
        

class PaymentDetailView(APIView):

    @method_decorator(ratelimit(key='user', rate='60/m', method='GET', block=True))
    def get(self, request, booking_reference):
        booking = get_booking_by_reference(booking_reference, request.user)
        if not booking:
            return Response({
                "error": "Booking not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        payment = get_payment_by_booking(booking)
        if not payment:
            return Response({
                "error": "No payment found for this booking."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PaymentDetailSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentListView(APIView):

    @method_decorator(ratelimit(key='user', rate='30/m', method='GET', block=True))
    def get(self, request):
        payments = get_user_payments(request.user)
        serializer = PaymentDetailSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)