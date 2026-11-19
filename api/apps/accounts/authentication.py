"""JWT in an httpOnly cookie. SimpleJWT creates and validates tokens;
we only carry them in a cookie, so JavaScript on the page can never read the token (XSS attacks)."""

from django.conf import settings
from django.http import HttpResponseBase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken


class CookieJWTAuthentication(JWTAuthentication):
    """Like JWTAuthentication, but reads the token from a cookie instead of the header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_NAME)
        if not raw_token:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except AuthenticationFailed:
            return None


def set_auth_cookie(response: HttpResponseBase, user) -> None:
    token = AccessToken.for_user(user)
    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        str(token),
        max_age=int(AccessToken.lifetime.total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookie(response: HttpResponseBase) -> None:
    response.delete_cookie(
        settings.AUTH_COOKIE_NAME,
        path="/",
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
