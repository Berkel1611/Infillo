"""Business rules of the accounts app; views stay thin and only call these functions."""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction

from apps.accounts.models import (
    MODERATORS_GROUP,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ShippingAddress,
)
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
        # Two registrations raced past the check above; the UNIQUE constraint caught it
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


def filter_users_by_role(queryset, role: str):
    """Same meaning as User.role: superuser -> admin, member of "moderators" -> moderator."""
    if role == ROLE_ADMIN:
        return queryset.filter(is_superuser=True)
    queryset = queryset.filter(is_superuser=False)
    if role == ROLE_MODERATOR:
        return queryset.filter(groups__name=MODERATORS_GROUP)
    return queryset.exclude(groups__name=MODERATORS_GROUP)  # ROLE_USER


def set_role(user, role: str) -> None:
    """user <-> moderator: the role is membership in the "moderators" group."""
    group = Group.objects.get(name=MODERATORS_GROUP)
    if role == ROLE_MODERATOR:
        user.groups.add(group)
    else:
        user.groups.remove(group)


def set_active(user, is_active: bool) -> None:
    """Blocks or unblocks. Takes effect at once: authentication loads the user on each request."""
    user.is_active = is_active
    user.save(update_fields=["is_active"])


def update_user_by_admin(actor, target, *, role: str | None = None, is_active: bool | None = None):
    """Role and block changes made by an administrator."""
    if target.pk == actor.pk:
        raise AppError("CANNOT_MODIFY_SELF", 400)
    if target.is_superuser:
        raise AppError("CANNOT_MODIFY_ADMIN", 400)
    with transaction.atomic():  # both changes or none
        if role is not None:
            set_role(target, role)
        if is_active is not None:
            set_active(target, is_active)
    return target
