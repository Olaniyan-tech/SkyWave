import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from celery import shared_task
from django.conf import settings
from users.constants import get_brevo_api, BREVO_SENDER
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id):
    from bookings.models import Booking

    try:
        booking = Booking.objects.select_related("user").get(id=booking_id)
    except Booking.DoesNotExist:
        logger.error("Booking %s not found, skipping confirmation email", booking_id)
        return
    
    try:
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": booking.user.email, "name": booking.user.username}],
            sender=BREVO_SENDER,
            subject=f"Booking Confirmation - {booking.booking_reference} ✈️",
            html_content=f"""
                <h2>Hi {booking.user.username},</h2>
                <p>Your booking has been created successfully!</p>
                <table style="border-collapse: collapse; width: 100%; margin-top: 16px 0;">
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Booking Reference</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.booking_reference}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Flight</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.airline_name} {booking.flight_number}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>From</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.origin_airport}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>To</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.destination_airport}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Departure</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.departure_time.strftime('%d %b %Y at %H:%M')}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Arrival</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.arrival_time.strftime('%d %b %Y at %H:%M')}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Duration</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.flight_duration}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Cabin Class</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.cabin_class.title()}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Passengers</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.passenger_count}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Total Amount</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.total_amount} {booking.currency}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Status</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">PENDING — Awaiting Payment</td></tr>
                </table>
                <p>Please proceed to payment to complete your booking.</p>
                <p><strong>SkyWave Team</strong></p>
            """
        )
        get_brevo_api().send_transac_email(send_smtp_email)
        logger.info(f"Booking confirmation email sent to %s", booking.booking_reference)

    except ApiException as exc:
        logger.error(f"Error occurred while sending booking confirmation email to %s: %s", booking_id, exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_booking_cancelled_email(self, booking_id):
    from bookings.models import Booking

    try:
        booking = Booking.objects.select_related("user").get(id=booking_id)
    except Booking.DoesNotExist:
        logger.error("Booking %s not found, skipping confirmation email", booking_id)
        return
    
    try:
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": booking.user.email, "name": booking.user.username}],
            sender=BREVO_SENDER,
            subject=f"Booking Cancelled - {booking.booking_reference} ❌",
            html_content=f"""
                <h2>Hi {booking.user.username},</h2>
                <p>Your booking has been cancelled.</p>
                <table style="border-collapse: collapse; width: 100%; margin-top: 16px 0;">
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Booking Reference</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.booking_reference}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Flight</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.airline_name} {booking.flight_number}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>From</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.origin_airport}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>To</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.destination_airport}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Departure</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.departure_time.strftime('%d %b %Y at %H:%M')}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Total Amount</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">{booking.total_amount}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><strong>Status</strong></td><td style="padding: 8px; border: 1px solid #e5e7eb;">CANCELLED</td></tr>
                </table>
                <p>If you paid for this booking, a refund will be processed within 5-7 business days. Please contact our support team if you have any questions.</p>
                <p><strong>SkyWave Team</strong></p>
            """
        )
        get_brevo_api().send_transac_email(send_smtp_email)
        logger.info(f"Booking cancellation email sent to %s", booking.booking_reference)

    except ApiException as exc:
        logger.error(f"Error occurred while sending booking cancellation email to %s: %s", booking_id, exc)
        raise self.retry(exc=exc, countdown=60)