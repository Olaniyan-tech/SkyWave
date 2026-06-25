from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CookieJWTAuthentication(JWTAuthentication):
     def authenticate(self, request):
          raw_token = request.COOKIES.get("access_token")
          if raw_token is None:
               return None
          
          try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
          
          except (TokenError, InvalidToken):
              raise AuthenticationFailed("Access token is invalid or expired. Please log in again.")

# class CookieJWTAuthenticationExtension(OpenApiAuthenticationExtension):
#     target_class = "users.authentication.CookieJWTAuthentication"
#     name = "CookieJWTAuthentication"

#     def get_security_definition(self, auto_schema):
#         return {
#             "type": "apiKey",
#             "in": "cookie",
#             "name": "access_token"
#         }