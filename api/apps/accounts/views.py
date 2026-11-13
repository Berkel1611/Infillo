from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.authentication import clear_auth_cookie, set_auth_cookie
from apps.accounts.serializers import LoginSerializer, RegisterSerializer, UserSerializer
from apps.accounts.services import authenticate_user, register_user


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


class MeView(generics.RetrieveAPIView):
    """The current user (default authentication and IsAuthenticated apply)."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
