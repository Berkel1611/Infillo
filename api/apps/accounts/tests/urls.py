"""URLconf for authentication tests: the real routes plus views that use the defaults."""

from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsModeratorOrAdmin
from config.urls import handler404, handler500, urlpatterns  # noqa: F401 (handlers are read by Django)


@api_view(["GET"])  # no decorators for auth or permissions: the project defaults apply
def whoami(request: Request) -> Response:
    return Response({"email": request.user.email, "role": request.user.role})


@api_view(["GET"])
@permission_classes([AllowAny])
def public(request: Request) -> Response:
    return Response({"authenticated": request.user.is_authenticated})


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_only(request: Request) -> Response:
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsModeratorOrAdmin])
def staff_only(request: Request) -> Response:
    return Response({"ok": True})


urlpatterns = [
    *urlpatterns,
    path("test/whoami", whoami),
    path("test/public", public),
    path("test/admin-only", admin_only),
    path("test/staff-only", staff_only),
]
