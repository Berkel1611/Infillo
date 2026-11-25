from rest_framework.request import Request

from apps.accounts.permissions import IsModeratorOrAdmin
from apps.catalog.models import Product
from apps.catalog.services import managed_category_ids
from apps.core.exceptions import AppError


class CanManageProduct(IsModeratorOrAdmin):
    """Moderators and admins may write; on a concrete product also its category must be
    in the user's scope (admin: everything, moderator: assigned categories and below)."""

    def has_object_permission(self, request: Request, view, obj: Product) -> bool:
        if obj.category_id in managed_category_ids(request.user):
            return True
        # Raised here (not just False) so the client gets our business code, not a bare 403
        raise AppError("CATEGORY_NOT_MANAGED", 403)
