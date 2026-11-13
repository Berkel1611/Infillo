from django.db import DatabaseError, connection
from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])  # public endpoint: skip auth entirely
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        database = "ok"
    except DatabaseError:
        database = "error"
    return Response({"status": "ok", "database": database})


def not_found(request: HttpRequest, exception: Exception) -> JsonResponse:
    """Unknown URL (handler404; used only when DEBUG = False)."""
    return JsonResponse({"code": "NOT_FOUND"}, status=404)


def server_error(request: HttpRequest) -> JsonResponse:
    """Unhandled exception (handler500); never exposes exception details."""
    return JsonResponse({"code": "INTERNAL_ERROR"}, status=500)
