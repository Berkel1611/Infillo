"""Business rules of the accounts app; views stay thin and only call these functions."""

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction

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
