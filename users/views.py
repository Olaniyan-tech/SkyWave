from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import (
    RegisterSerializer, 
    UserSerializer,
    RequestPasswordResetSerializer,
    ConfirmPasswordResetSerializer
)
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from django.contrib.auth import get_user_model
from users.services.token_services import (
    send_email_verification, 
    verify_user_email,
    create_password_reset_token,
    reset_user_password
)
from users.selectors import (
    get_user_by_email,
    get_email_verification_token, 
    get_password_reset_token
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging
from django.conf import settings


DEBUG = settings.DEBUG
logger = logging.getLogger(__name__)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True))
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                send_email_verification(user)
                logger.info(f"New user registered: {user.email if hasattr(user, 'email') else user.username}")
                return Response({
                    "message": "Account created successfully. Please log in to continue",
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone},
                    status=status.HTTP_201_CREATED)
        
            logger.warning(f"Registration failed: {serializer.errors}")
            return Response({
                "message": "Registration failed. Check input.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("Unexpected error during registration")
            return Response({
                "message": "Server error occurred during registration"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = TokenObtainPairSerializer

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        try: 
            response_data = super().post(request, *args, **kwargs).data

            response = Response({"message" : "Login successful"}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=response_data['access'],
                httponly=True,
                samesite='Lax' if DEBUG else 'None',
                secure=not DEBUG,
                max_age=30*60, #30 minutes
                path='/'
            )

            response.set_cookie(
                key='refresh_token',
                value=response_data['refresh'],
                httponly=True,
                samesite='Lax' if DEBUG else 'None',
                secure=not DEBUG,
                max_age=7*24*60*60, # 7 days
                path='/'
            )
            return response
        
        except InvalidToken:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except AuthenticationFailed:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({"error": "Login failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='30/m', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        if request.data.get("refresh"):
            return Response({"error": "Do not send a refresh token in body"}, status=status.HTTP_400_BAD_REQUEST)
        
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error" : "Refresh token not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            serializer = self.get_serializer(data={"refresh": refresh_token})
            serializer.is_valid(raise_exception=True)
            new_access = serializer.validated_data['access']

            response = Response({"message": "Access token refreshed"}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=new_access,
                httponly=True,
                samesite='Lax' if DEBUG else 'None',
                secure=not DEBUG,
                max_age=30*60,
                path='/'
            )
            
            return response
        
        except TokenError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Refresh token error: {str(e)}")
            return Response({"error": "Could not refresh token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='30/m', method='POST', block=True))
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info("Refresh token blacklisted")
            except TokenError:
                logger.warning("Refresh token already invalid")
            except Exception as e:
                logger.error(f"Unexpected error during logout: {str(e)}")
        
        response = Response({"message" : "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token", path='/')
        response.delete_cookie("refresh_token", path='/')
        response['Cache-Control'] = 'no-store, must-revalidate'

        return response


class UserProfileView(generics.GenericAPIView):

    """
    GET  /api/users/me/   — fetch own profile
    PATCH /api/users/me/  — update own profile 
    """
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    @method_decorator(ratelimit(key='user', rate='60/m', method='GET', block=True), name='get')
    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @method_decorator(ratelimit(key='user', rate='10/m', method='PATCH', block=True), name='patch')    
    def patch(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='20/h', method='GET', block=True))
    def get(self, request):
        token = request.query_params.get("token", "").strip()

        if not token:
            return Response(
                {"error": "Verification token is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token_obj = get_email_verification_token(token)
        if not token_obj:
            return Response(
                {"error": "Invalid verification token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            verify_user_email(token_obj)
        except DjangoValidationError as e:
            return Response(
                {"error": e.message if e.message else str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            logger.error(f"Email verification error")
            return Response(
                {
                    "error": "Email verification failed",
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {"message": "Email verified successfully. You can now book flights."}, 
            status=status.HTTP_200_OK
        )


class ResendVerificationEmailView(APIView):
    """
    User didn't receive or the link expired.
    They request a new verification email.
    Must be logged in — we know who they are from the cookie.
    """

    @method_decorator(ratelimit(key='user', rate='3/h', method='POST', block=True))
    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response(
                {"message": "Your email is now verified."}, 
                status=status.HTTP_200_OK
            )

        token = get_email_verification_token(user)
        if not token:
            return Response(
                {"error": "Could not generate verification token. Please try again."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            send_email_verification(user, token)
            logger.info(f"Resent verification email to {user.email}")
            return Response(
                {"message": "Verification email resent. Please check your inbox."}, 
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error resending verification email to {user.email}: {str(e)}")
            return Response(
                {"error": "Failed to resend verification email. Please try again later."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class RequestPasswordResetView(APIView):
    """
    User forgot their password.
    We always return success even if email not found —
    this prevents attackers from knowing which emails exist.
    No authentication required — user is logged out.
    """
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True))
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
         
        email = serializer.validated_data['email']

        user = get_user_by_email(email)
        if user:
            create_password_reset_token(user)

        # Always return success response to prevent email enumeration
        return Response(
            {"message": "If an account with that email exists, a password reset link has been sent."}, 
            status=status.HTTP_200_OK
        )


class ConfirmPasswordResetView(APIView):
    """
    User clicks the link in email → sees form → submits new password.
    We validate the token and save the new password.
    No authentication required — user is logged out.
    """
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def post(self, request):
        serializer = ConfirmPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        confirm_password = serializer.validated_data['confirm_password']

        # Find token in database
        token_obj = get_password_reset_token(token)
        if not token_obj:
            return Response(
                {"error": "Invalid or expired password reset token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            reset_user_password(token_obj, new_password, confirm_password)
            logger.info(f"Password reset successful for {token_obj.user.email}")
            return Response(
                {"message": "Password reset successful. You can now log in with your new password."}, 
                status=status.HTTP_200_OK
            )
        
        except DjangoValidationError as e:
            return Response(
                {"error": e.message if e.message else str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Password reset error for {token_obj.user.email}: {str(e)}")
            return Response(
                {"error": "Failed to reset password. Please try again later."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )