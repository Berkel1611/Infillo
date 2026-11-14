"""Business rules of the accounts app; views stay thin and only call these functions."""

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction

from apps.accounts.models import ShippingAddress
from apps.core.exceptions import AppError

User = get_user_model()


def _ensure_not_taken(email: str, username: str) -> None:
    if User.objects.filter(email=email).exists():
        raise AppError("EMAIL_TAKEN", 409)
    if User.objects.filter(username__iexact=username).exists():
        raise AppError("USERNAME_TAKEN", 409)


def register_user(*, email: str, username: str, password: str, first_name: str, last_name: str):
    """Creates a regular user (role "user": no group, not a superuser.)"""
    _ensure_not_taken(email, username)
    try:
        # atomic() = savepoint: a failed INSERT must not break outer transaction
        with transaction.atomic():
            return User.objects.create_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
    except IntegrityError:
        # Two registrations raced past the ckech above; the UNIQUE constraint caught it
        _ensure_not_taken(email, username)
        raise


def authenticate_user(*, login: str, password: str):
    """Unknown account, wrong password, blocked account and password account all look the same."""
    user = authenticate(username=login, password=password)
    if user is None:
        raise AppError("INVALID_CREDENTIALS", 401)
    return user


def update_profile(user, **fields):
    """Changes username, first name and / or last name (PATCH: only the given fields)."""
    if "username" in fields:
        fields["username"] = User.normalize_username(fields["username"])  # as in create_user
        # Own account excluded: changing only the letter case of your own name is allowed
        if User.objects.filter(username__iexact=fields["username"]).exclude(pk=user.pk).exists():
            raise AppError("USERNAME_TAKEN", 409)
    for name, value in fields.items():
        setattr(user, name, value)
    try:
        with transaction.atomic():
            user.save(update_fields=list(fields))  # an empty list = nothing to write
    except IntegrityError:
        # Another request took the name between the check and the UPDATE
        raise AppError("USERNAME_TAKEN", 409) from None
    return user


def save_shipping_address(user, **fields) -> ShippingAddress:
    """Creates or overwrites the user's single address."""
    address, _created = ShippingAddress.objects.update_or_create(user=user, defaults=fields)
    return address
