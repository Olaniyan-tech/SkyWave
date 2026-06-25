from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from users.models import EmailVerificationToken, PasswordResetToken
from users.tokens import (
    generate_token,
    get_email_verification_token_expiry,
    get_password_reset_token_expiry,
)
from users.tasks import (
    send_verification_email,
    send_welcome_email,
    send_password_reset_email,
)
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


def send_email_verification(user):
    # Delete old token if it exists
    EmailVerificationToken.objects.filter(user=user).delete()

    # Generate a new secure token and save it
    token = generate_token()
    EmailVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=get_email_verification_token_expiry()
    )

    # Send the email — if this fails we log it but don't crash
    # the user is already registered, they can request a new email
    try:
        send_verification_email.delay(user.id, token)
        logger.info("Email verification sent to %s", user.email)
    except Exception as e:
        logger.error("Failed to send verification email to %s: %s", user.email, e)


def verify_user_email(token_obj):
    if token_obj.is_expired():
        raise ValidationError("Verification link has expired. Please request a new one.")
    
    with transaction.atomic():
        user = token_obj.user
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=['email_verified', 'is_active'])
        token_obj.delete()  # Remove the token after successful verification
    
    try:
        send_welcome_email.delay(user.id)
        logger.info("Welcome email sent to %s", user.email)
    except Exception as e:
        logger.error("Failed to send welcome email to %s: %s", user.email, e)
    
    return user


def create_password_reset_token(user):
    # Delete old token if it exists
    PasswordResetToken.objects.filter(user=user).delete()

    # Create new token
    token = generate_token()
    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=get_password_reset_token_expiry()
    )

    try:
        send_password_reset_email.delay(user.id, token)
        logger.info("Password reset email sent to %s", user.email)
    except Exception as e:
        logger.error("Failed to send password reset email to %s: %s", user.email, e)


def reset_user_password(token_obj, new_password, confirm_password):
    if token_obj.is_expired():
        raise ValidationError("Password reset link has expired. Please request a new one.")

    if new_password != confirm_password:
        raise ValidationError("Passwords do not match.")

    try:
        validate_password(new_password, token_obj.user)
    except ValidationError as e:
        raise ValidationError({"new_password": e.messages})

    with transaction.atomic():
        user = token_obj.user
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
        token_obj.delete()  # Remove the token after successful password reset
    
    logger.info("Password reset successful for %s", user.email) 
    return user