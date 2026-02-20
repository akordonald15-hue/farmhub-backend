from django.conf import settings
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access_cookie = settings.SIMPLE_JWT.get("ACCESS_COOKIE_NAME", "access_token")
        raw_token = request.COOKIES.get(access_cookie)

        if raw_token:
            validated_token = self.get_validated_token(raw_token)
            if request.method not in SAFE_METHODS:
                SessionAuthentication().enforce_csrf(request)
            return self.get_user(validated_token), validated_token

        if settings.DEBUG:
            return super().authenticate(request)

        return None
