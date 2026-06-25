import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS', 24)
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 1)

def generate_token():
    return secrets.token_urlsafe(32)

def get_email_verification_token_expiry():
    return timezone.now() + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS)

def get_password_reset_token_expiry():
    return timezone.now() + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS)

def is_token_expired(expiry_datetime):
    return timezone.now() > expiry_datetime
