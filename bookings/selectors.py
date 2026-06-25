from bookings.models import Booking
from django.db.models import Sum

def get_user_bookings(user, booking_status=None, payment_status=None, trip_type=None):
    qs = Booking.objects.filter(user=user).prefetch_related('passengers')

    if booking_status:
        qs = qs.filter(booking_status=booking_status.upper())
    if payment_status:
        qs = qs.filter(payment_status=payment_status.upper())
    if trip_type:
        qs = qs.filter(trip_type=trip_type.upper())
    
    return qs

def get_booking_by_reference(booking_reference, user):
    try:
        return Booking.objects.prefetch_related('passengers').get(
            booking_reference=booking_reference,
            user=user
        )
    
    except Booking.DoesNotExist:
        return None

def get_booking_stats(user):
    bookings = Booking.objects.filter(user=user)

    total_spent = bookings.filter(payment_status="PAID").aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    return {
        "total": bookings.count(),
        "pending": bookings.filter(booking_status="PENDING").count(),
        "confirmed": bookings.filter(booking_status="CONFIRMED").count(),
        "cancelled": bookings.filter(booking_status="CANCELLED").count(),
        "completed": bookings.filter(booking_status="COMPLETED").count(),
        "failed": bookings.filter(booking_status="FAILED").count(),
        "total_spent": str(total_spent),
    }
