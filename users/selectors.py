from django.contrib.auth import get_user_model
from users.models import EmailVerificationToken, PasswordResetToken


User = get_user_model()

def get_user_by_email(email):
    return User.objects.filter(email__iexact=email).first()

def get_email_verification_token(token):
    try:
        return EmailVerificationToken.objects.select_related('user').get(token=token)
    except EmailVerificationToken.DoesNotExist:
        return None

def get_password_reset_token(token):
    try:
        return PasswordResetToken.objects.select_related('user').get(token=token)
    except PasswordResetToken.DoesNotExist:
        return None