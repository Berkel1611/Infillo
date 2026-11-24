from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsModeratorOrAdmin
from apps.catalog.models import Category
from apps.catalog.serializers import (
    CategoryNodeSerializer,
    CategorySerializer,
    CategoryWriteSerializer,
    ModeratorAssignSerializer,
    ModeratorSerializer,
)
from apps.catalog.services import (
    build_category_tree,
    category_moderators,
    create_category,
    delete_category,
    managed_category_ids,
    set_category_moderators,
    update_category,
)
from apps.core.exceptions import AppError


class CategoryViewSet(viewsets.GenericViewSet):
    """GET /categories is public; creating, editing and deleting is for administrators."""

    queryset = Category.objects.all()
    pagination_class = None  # the whole tree is returned at once

    def get_permissions(self):
        # DRF wants instances here, not classes
        if self.action == "list":
            return [AllowAny()]
        if self.action == "managed":
            return [IsModeratorOrAdmin()]
        return [IsAdmin()]

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise AppError("CATEGORY_NOT_FOUND", 404) from None

    def list(self, request: Request) -> Response:
        return Response(CategoryNodeSerializer(build_category_tree(), many=True).data)

    def create(self, request: Request) -> Response:
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = create_category(
            serializer.validated_data["name"], serializer.validated_data.get("parent_id")
        )
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        category = self.get_object()
        serializer = CategoryWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = update_category(category, serializer.validated_data)
        return Response(CategorySerializer(category).data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        delete_category(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def managed(self, request: Request) -> Response:
        """Flat list of the categories the current user manages products in."""
        categories = Category.objects.filter(pk__in=managed_category_ids(request.user))
        return Response(CategorySerializer(categories, many=True).data)

    @action(detail=True, methods=["get", "put"])
    def moderators(self, request: Request, *args, **kwargs) -> Response:
        category = self.get_object()
        if request.method == "PUT":
            serializer = ModeratorAssignSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            moderators = set_category_moderators(
                category, serializer.validated_data["moderator_ids"]
            )
        else:
            moderators = category_moderators(category)
        return Response(ModeratorSerializer(moderators, many=True).data)
