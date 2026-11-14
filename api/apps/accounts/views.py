from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.authentication import clear_auth_cookie, set_auth_cookie
from apps.accounts.models import ShippingAddress
from apps.accounts.serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ShippingAddressSerializer,
    UserSerializer,
)
from apps.accounts.services import (
    authenticate_user,
    register_user,
    save_shipping_address,
    update_profile,
)


class RegisterView(APIView):
    # No authentication classes: otherwise an expired cookie would block registration (401)
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(**serializer.validated_data)
        response = Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        set_auth_cookie(response, user)
        return response


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_user(**serializer.validated_data)
        response = Response(UserSerializer(user).data)
        set_auth_cookie(response, user)
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookie(response)
        return response


class MeView(APIView):
    """The current user (default authentication and IsAuthenticated apply)."""

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)

    def patch(self, request: Request) -> Response:
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_profile(request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data)


class MyAddressView(APIView):
    def get(self, request: Request) -> Response:
        address = ShippingAddress.objects.filter(user=request.user).first()
        if address is None:
            # DRF renders Response(None) as an empty body; the contract says JSON null
            return JsonResponse(None, safe=False)
        return Response(ShippingAddressSerializer(address).data)

    def put(self, request: Request) -> Response:
        serializer = ShippingAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = save_shipping_address(request.user, **serializer.validated_data)
        return Response(ShippingAddressSerializer(address).data)
