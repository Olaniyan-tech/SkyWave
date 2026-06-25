import uuid
import time
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from payments.models import Payment
from payments.tasks import send_payment_email
import logging

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15


def _get_timeout():
    try:
        return int(getattr(settings, "PAYSTACK_TIMEOUT", DEFAULT_TIMEOUT))
    except (ValueError, TypeError):
        logger.warning("Invalid PAYSTACK_TIMEOUT value. Using default timeout.")
        return DEFAULT_TIMEOUT
    

def _build_paystack_headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }


def _request_json(method, url, retries=2, **kwargs):
    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, timeout=_get_timeout(), **kwargs)
            return response, response.json()
        except requests.RequestException as e:
            if attempt == retries:
                logger.exception("Paystack request failed after retries.")
                raise ValidationError("Payment service is currently unavailable. Please try again later.") from e
            time.sleep(2 ** attempt)  # wait 1s, then 2s before retrying


def _apply_payment_result(payment, paystack_status, payment_data):
    if payment.payment_status == "PAID":
        logger.info(
            "Payment %s already marked PAID — skipping duplicate update",
            payment.payment_reference
        )
        return False
    
    with transaction.atomic():
        if paystack_status == "success":
            authorization = payment_data.get("authorization", {})

            payment.payment_status = "PAID"
            payment.paystack_reference = payment_data.get("reference", "")
            payment.payment_method = payment_data.get("channel", "").upper()
            payment.channel = payment_data.get("channel", "")
            payment.card_last_four = authorization.get("last4", "")
            payment.card_brand = authorization.get("brand", "")
            payment.paystack_response = payment_data
            payment.paid_at = timezone.now()
            payment.save(update_fields=[
                "payment_status", "paystack_reference", "payment_method", 
                "channel", "card_last_four", "card_brand", 
                "paystack_response", "paid_at", "updated_at"
            ])

            booking = payment.booking
            booking.payment_status = "PAID"
            booking.booking_status = "CONFIRMED"
            booking.save(update_fields=["payment_status", "booking_status", "updated_at"])

            logger.info(
                "Payment verified successfully for reference %s - booking %s by user %s",
                payment.payment_reference, 
                booking.booking_reference, 
                booking.user.username,
            )
            
        elif paystack_status == "failed":
            payment.payment_status = "FAILED"
            payment.paystack_response = payment_data
            payment.save(update_fields=["payment_status", "paystack_response", "updated_at"])

            booking = payment.booking
            booking.payment_status = "FAILED"
            booking.save(update_fields=["payment_status", "updated_at"])

            logger.warning(
                "Payment verification failed for reference %s - booking %s by user %s", 
                payment.payment_reference,
                payment.booking.booking_reference, 
                payment.booking.user.username
            )
    
    send_payment_email.delay(payment.booking.id, payment.payment_status)
    return True


def initialize_payment(booking):
    if booking.payment_status == "PAID":
        raise ValidationError("This booking has already been paid for.")
    
    if booking.booking_status == "CANCELLED":
        raise ValidationError("Cannot initialize payment for a cancelled booking.")
    
    if booking.total_amount <= 0:
        raise ValidationError("Booking amount must be greater than 0.")
    
    if not booking.user.email:
        raise ValidationError("A valid email is required for payment.")
    
    if hasattr(booking, "payment") and booking.payment.payment_status == "PENDING":
        raise ValidationError("Payment has already been initialized for this booking.")
    
    payment_reference = f"PAY-{booking.booking_reference}-{uuid.uuid4().hex[:6].upper()}"

    payload = {
        "email": booking.user.email,
        "amount": int(booking.total_amount * 100),  # Paystack uses kobo
        "reference": payment_reference,
        "callback_url": f"{settings.PAYSTACK_CALLBACK_URL}?reference={payment_reference}",
        "metadata": {
            "booking_reference": str(booking.booking_reference),
            "user_id": str(booking.user.id),
            "username": booking.user.username
        }
    }

    response, data = _request_json(
        "POST", 
        f"{settings.PAYSTACK_BASE_URL}/transaction/initialize", 
        json=payload, 
        headers=_build_paystack_headers()
    )

    if not response.ok:
        logger.warning(
            "Paystack initialize failed for booking=%s status=%s",
            booking.booking_reference, response.status_code
        )
        raise ValidationError("Payment initialization failed. Please try again.")
    
    if not data.get("status"):
        logger.warning(
            "Paystack initialize error for booking=%s error=%s",
            booking.booking_reference, data.get("message")
        )
        raise ValidationError(data.get("message", "Payment initialization failed. Please try again."))
    
    try:
        authorization_url = data["data"]["authorization_url"]
        paystack_reference = data["data"]["reference"]
    except (TypeError, KeyError):
        logger.exception("Unexpected Paystack response structure for booking=%s", booking.booking_reference)
        raise ValidationError("Payment initialization failed due to an unexpected response. Please try again.")
    
    with transaction.atomic():
        Payment.objects.create(
            booking=booking,
            payment_reference=payment_reference,
            paystack_reference=paystack_reference,
            amount=booking.total_amount,
            currency=booking.currency,
            payment_status="PENDING"
        )

        booking.payment_status = "PENDING"
        booking.save(update_fields=["payment_status", "updated_at"])

    logger.info(
        "Payment initialized for booking %s by user %s - ref: %s", 
        booking.booking_reference, 
        booking.user.username, 
        payment_reference
    )
    return authorization_url, payment_reference


def verify_payment(reference):
    if not reference:
        raise ValidationError("Payment reference is required for verification.")
    
    try:
        payment = Payment.objects.select_related(
            "booking", "booking__user"
        ).get(payment_reference=reference)

    except Payment.DoesNotExist:
        logger.warning("Payment verification failed - reference not found: %s", reference)
        raise ValidationError("Payment record not found.")
    
    if payment.payment_status == "PAID":
        logger.info("Payment already verified for reference: %s", reference)
        raise ValidationError("Payment has already been verified.")
        
    response, data = _request_json(
        "GET",
        f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=_build_paystack_headers()
    )

    if response.status_code != 200:
        logger.warning(
            "Paystack verify failed for reference=%s status=%s", 
            reference, response.status_code
        )
        raise ValidationError("Payment verification failed. Please try again.")
    
    if not data.get("status"):
        logger.warning(
            "Paystack verify error for reference=%s error=%s", 
            reference, data.get("message")
        )
        raise ValidationError(data.get("message", "Payment verification failed. Please try again."))
    
    try:
        payment_data = data["data"]
    except (TypeError, KeyError):
        logger.exception("Unexpected Paystack response structure during verification for reference=%s", reference)
        raise ValidationError("Payment verification failed due to an unexpected response. Please try again.")
    
    paystack_status = payment_data.get("status")
    _apply_payment_result(payment, paystack_status, payment_data)
    
    return payment_data


def handle_webhook_payment_update(payment, paystack_status, payment_data):
    """
    Called by the Paystack webhook view.
    payment        — Payment object found by reference
    paystack_status — "PAID" or "FAILED" mapped from the webhook event
    payment_data   — raw webhook payload data
    """
    # Map webhook status naming to match what _apply_payment_result expects
    status_map = {"PAID": "success", "FAILED": "failed"}
    mapped_status = status_map.get(paystack_status, paystack_status)

    return _apply_payment_result(payment, mapped_status, payment_data)