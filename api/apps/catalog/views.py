from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin
from apps.catalog.models import Category
from apps.catalog.serializers import (
    CategoryNodeSerializer,
    CategorySerializer,
    CategoryWriteSerializer,
)
from apps.catalog.services import (
    build_category_tree,
    create_category,
    delete_category,
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
