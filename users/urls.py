from django.urls import path
from .views import(
    RegisterView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    UserProfileView,
    VerifyEmailView,
    ResendVerificationEmailView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
)

app_name = 'users'
urlpatterns = [
    # Auth 
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name="login"),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name="token_refresh"),
    path('logout/', LogoutView.as_view(), name='logout'),
 
     # Profile 
    path('my_profile/', UserProfileView.as_view(), name="me"),
  
    # Email Verification 
    path('verify-email/',         VerifyEmailView.as_view(),              name='verify-email'),
    path('resend-verification/',  ResendVerificationEmailView.as_view(),  name='resend-verification'),

    # Password Reset 
    path('password-reset/request/', RequestPasswordResetView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', ConfirmPasswordResetView.as_view(), name='password-reset-confirm'),


]