from django.db import DatabaseError, connection
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
