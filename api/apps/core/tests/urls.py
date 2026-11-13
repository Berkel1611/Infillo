"""URLconf for error contract tests: the real routes plus views that fail on purpose."""

from django.urls import path
from rest_framework import serializers
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import AppError
from config.urls import handler404, handler500, urlpatterns  # noqa: F401 (handlers are read by Django)


class SampleSerializer(serializers.Serializer):
    email = serializers.EmailField()
    quantity = serializers.IntegerField(min_value=1)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def validate(request: Request) -> Response:
    serializer = SampleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def app_error(request: Request) -> Response:
    raise AppError("OUT_OF_STOCK", 409, available=2)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def boom(request: Request) -> Response:
    raise RuntimeError("secret detail")


urlpatterns = [
    *urlpatterns,
    path("test/validate", validate),
    path("test/app-error", app_error),
    path("test/boom", boom),
]
