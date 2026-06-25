from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from bookings.serializers import (
    BookingCreateSerializer, 
    BookingListSerializer,
    BookingDetailSerializer
)
from bookings.selectors import (
    get_user_bookings, 
    get_booking_by_reference, 
    get_booking_stats
)
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from bookings.services.booking_service import create_booking, cancel_booking
import logging


logger = logging.getLogger(__name__)


class BookingCreateView(APIView):

    @method_decorator(ratelimit(key='user', rate='10/m', method='POST', block=True))
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )

        result = create_booking(
            user=request.user,
            offer_id=serializer.validated_data["offer_id"],
            passengers_data=serializer.validated_data["passengers"]
        )

        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "message": "Booking created successfully. Please proceed to payment.",
            "booking": BookingDetailSerializer(result["booking"]).data,},
            status=status.HTTP_201_CREATED
        )


@method_decorator(ratelimit(key='user', rate='30/m', method='GET', block=True), name='dispatch')
class BookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer

    def get_queryset(self):
        return get_user_bookings(
            user=self.request.user,
            booking_status=self.request.query_params.get("booking_status"),
            payment_status=self.request.query_params.get("payment_status"),
            trip_type=self.request.query_params.get("trip_type"),
        )


class BookingDetailView(APIView):

    @method_decorator(ratelimit(key='user', rate='60/m', method='GET', block=True))
    def get(self, request, booking_reference):
        booking = get_booking_by_reference(booking_reference, request.user)

        if not booking:
            return Response(
                {"error": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_200_OK
        )


class BookingCancelView(APIView):

    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
    def post(self, request, booking_reference):
        booking = get_booking_by_reference(booking_reference, request.user)

        if not booking:
            return Response(
                {"error": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        result = cancel_booking(booking)

        if not result["success"]:
            return Response(
                {"error": result["error"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "message": result["message"],
            "booking_reference": booking_reference,
            "booking_status": booking.booking_status},
            status=status.HTTP_200_OK
        )


class BookingStatsView(APIView):

    @method_decorator(ratelimit(key='user', rate='30/m', method='GET', block=True))
    def get(self, request):
        stats = get_booking_stats(request.user)
        return Response(stats, status=status.HTTP_200_OK)