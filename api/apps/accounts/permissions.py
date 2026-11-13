from rest_framework.permissions import BasePermission

from apps.accounts.models import ROLE_ADMIN, ROLE_MODERATOR


class IsAdmin(BasePermission):
    """Administrator = superuser."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)


class IsModeratorOrAdmin(BasePermission):
    """Moderator = member of the "moderators" group, Admin = superuser."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in (ROLE_MODERATOR, ROLE_ADMIN))
