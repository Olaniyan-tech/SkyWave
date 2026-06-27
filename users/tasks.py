from celery import shared_task
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
from django.contrib.auth import get_user_model
from users.constants import get_brevo_api, BREVO_SENDER
import logging


logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(max_retries=3)
def send_verification_email(user_id, token):
    try:
        user = User.objects.get(id=user_id)

        verification_url = f"{settings.BACKEND_URL}/api/users/verify-email/?token={token}"

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.username}],
            sender=BREVO_SENDER,
            subject="Verify Your Email Address",
            html_content=f"""
                <h2>Hi {user.username},</h2>
                <p>Welcome to SkyWave! Please click the link below to verify your email address:</p>
                <a href="{verification_url}" style="
                    background-color: #2563eb;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    display: inline-block;
                    margin: 16px 0;
                ">Verify Email</a>
                <p>Or copy this link: {verification_url}</p>
                <p>This link expires in 24 hours.</p>
                <p>If you did not create an account, please ignore this email.</p>
                <p><strong>SkyWave Team</strong></p>
            """
        )
        get_brevo_api().send_transac_email(send_smtp_email)
        logger.info("Verification email sent to %s", user.email)
    
    except User.DoesNotExist:
        logger.error("User not found for verification email (id=%s)", user_id)

    except ApiException as e:
        logger.error("Error occurred while sending verification email to %s: %s", user.email, e)
        raise


@shared_task(max_retries=3)
def send_welcome_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.username}],
            sender=BREVO_SENDER,
            subject="Welcome to SkyWave! 🎉",
            html_content=f"""
                <h2>Hi {user.username},</h2>
                <p>Your email has been verified successfully. Welcome to SkyWave!</p>
                <p>You can now:</p>
                <ul>
                    <li>Search for flights globally</li>
                    <li>Book flights in minutes</li>
                    <li>Manage your bookings</li>
                </ul>
                <p><strong>SkyWave Team</strong></p>
            """
        )
        get_brevo_api().send_transac_email(send_smtp_email)
        logger.info(f"Welcome email sent to %s", user.email)

    except User.DoesNotExist:
        logger.error("User not found for verification email (id=%s)", user_id)

    except ApiException as e:
        logger.error("Error occurred while sending welcome email to %s: %s", user.email, e)
        raise


@shared_task(max_retries=3)
def send_password_reset_email(user_id, token):
    try:
        user = User.objects.get(id=user_id)

        reset_url = f"{settings.BACKEND_URL}/api/users/password-reset/confirm/?token={token}"

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.username}],
            sender=BREVO_SENDER,
            subject="Reset Your Password 🔐",
            html_content=f"""
                <h2>Hi {user.username},</h2>
                <p>We received a request to reset your password. Please click the link below to reset it:</p>
                <a href="{reset_url}" style="
                    background-color: #2563eb;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    display: inline-block;
                    margin: 16px 0;
                ">Reset Password</a>
                <p>Or copy this link: {reset_url}</p>
                <p>This link expires in 1 hour.</p>
                <p>If you did not request a password reset, please ignore this email.</p>
                <p><strong>SkyWave Team</strong></p>
            """
        )
        get_brevo_api().send_transac_email(send_smtp_email)
        logger.info("Password reset email sent to %s", user.email)

    except User.DoesNotExist:
        logger.error("User not found for password reset email (id=%s)", user_id)

    except ApiException as e:
        logger.error("Error occurred while sending password reset email to %s: %s", user.email, e)
        raise


