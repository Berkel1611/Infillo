from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import ShippingAddress, username_validator

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


class ProfileFieldsSerializer(serializers.Serializer):
    """Fields shared by registration and profile update (one set of rules for both)."""

    username = serializers.CharField(min_length=3, max_length=30, validators=[username_validator])
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=80)


class RegisterSerializer(ProfileFieldsSerializer):
    """Input only. A plain Serializer on purpose: uniqueness 
    is checked in services.py (-> 409)."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)

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


class ProfileUpdateSerializer(ProfileFieldsSerializer):
    """PATCH /auth/me. Used with partial=True: only the fields that were sent are required."""


class ShippingAddressSerializer(serializers.ModelSerializer):
    # Field rules come from the model
    class Meta:
        model = ShippingAddress
        fields = ("street", "postal_code", "city", "phone", "updated_at")
        read_only_fields = ("updated_at",)
