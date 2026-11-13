from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import username_validator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Output only. Never contains the password."""

    role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "date_joined",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """Input only."""

    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(min_length=3, max_length=30, validators=[username_validator])
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=80)

    def validate_email(self, value: str) -> str:
        return value.lower()

    def validate(self, attrs):
        candidate = User(
            email=attrs["email"],
            username=attrs["username"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {
                    "password": [
                        serializers.ErrorDetail(item.messages[0], code=item.code)
                        for item in error.error_list
                    ]
                }
            ) from error
        return attrs


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=254)
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
