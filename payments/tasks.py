from celery import shared_task
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from bookings.models import Booking
from django.conf import settings
from users.constants import get_brevo_api, BREVO_SENDER
import logging


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_payment_email(self, booking_id, payment_status):
    try:
        booking = Booking.objects.select_related('user').get(id=booking_id)
    except Booking.DoesNotExist:
        logger.error("Booking %s not found, skipping payment email", booking_id)
        return

    try:
        if payment_status == "PAID":
            subject = "Payment successful ✅"
            html_content = f"""
                <h2>Hi {booking.user.username},</h2>
                <p>Your payment of {booking.total_amount} {booking.currency} has been received successfully.</p>
                <p>Booking Reference: <strong>{booking.booking_reference}</strong></p>
                <p>Your flight from {booking.origin_airport} to {booking.destination_airport} is now confirmed.</p>
                <p>Thank you for choosing SkyWave</p>
                <p><strong>SkyWave Team</strong></p>
            """
        
        else:
            subject = "Payment failed ❌"
            html_content = f"""
                <h2>Hi {booking.user.username},</h2>
                <p>Unfortunately your payment for Booking {booking.booking_reference} failed.</p>
                <p>Please try again or contact support.</p>
                <p>SkyWave Team</p>
            """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": booking.user.email, "name": booking.user.username}],
            sender=BREVO_SENDER,
            subject=subject,
            html_content=html_content
        )

        get_brevo_api().send_transac_email(send_smtp_email)                
        logger.info("Payment email sent to %s — %s", booking.user.email, payment_status)

    except ApiException as exc:
        logger.error("Failed to send payment email for booking %s: %s", booking_id, exc)
        raise self.retry(exc=exc, countdown=60)