from django.db.models import Min, Q
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsModeratorOrAdmin
from apps.catalog.models import Category, Product
from apps.catalog.permissions import CanManageProduct
from apps.catalog.serializers import (
    CategoryNodeSerializer,
    CategorySerializer,
    CategoryWriteSerializer,
    ManagedProductRowSerializer,
    ModeratorAssignSerializer,
    ModeratorSerializer,
    ProductDetailSerializer,
    ProductListQuerySerializer,
    ProductRowSerializer,
    ProductWriteSerializer,
)
from apps.catalog.services import (
    build_category_tree,
    category_moderators,
    create_category,
    delete_category,
    descendant_ids,
    managed_category_ids,
    save_product,
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


class ProductViewSet(viewsets.GenericViewSet):
    """Public list and detail; creating and editing for moderators (own scope) and admins.
    There is no DELETE: a product is hidden with is_published=False."""

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "partial_update":
            return [CanManageProduct()]
        return [IsModeratorOrAdmin()]  # create, managed

    def get_queryset(self):
        # select_related / prefetch_related: category and variants for the whole page at once
        queryset = Product.objects.select_related("category").prefetch_related("variants")
        if self.action in ("retrieve", "partial_update"):
            # A draft is visible only to those who manage its category; for everybody else it
            # does not exist (404, not 403), so ids do not reveal unpublished products
            managed = managed_category_ids(self.request.user)
            return queryset.filter(Q(is_published=True) | Q(category_id__in=managed))
        return queryset

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise AppError("PRODUCT_NOT_FOUND", 404) from None

    def _page(self, queryset, serializer_class) -> Response:
        params = ProductListQuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        if (category_id := params.validated_data.get("category")) is not None:
            if not Category.objects.filter(pk=category_id).exists():
                raise AppError("CATEGORY_NOT_FOUND", 404)
            queryset = queryset.filter(category_id__in={category_id} | descendant_ids(category_id))
        if search := params.validated_data.get("search"):
            queryset = queryset.filter(name__icontains=search)
        queryset = queryset.annotate(price_from=Min("variants__price")).order_by("-id")

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(serializer_class(page, many=True).data)

    def list(self, request: Request) -> Response:
        return self._page(self.get_queryset().filter(is_published=True), ProductRowSerializer)

    @action(detail=False, methods=["get"])
    def managed(self, request: Request) -> Response:
        """Products in the user's scope, drafts included."""
        queryset = self.get_queryset().filter(category_id__in=managed_category_ids(request.user))
        return self._page(queryset, ManagedProductRowSerializer)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return Response(ProductDetailSerializer(self.get_object()).data)

    def _detail(self, product: Product) -> Response:
        # Read again: variants prefetched onto the instance would be stale after save_product
        queryset = Product.objects.select_related("category").prefetch_related("variants")
        return Response(ProductDetailSerializer(queryset.get(pk=product.pk)).data)

    def create(self, request: Request) -> Response:
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = save_product(request.user, data=serializer.validated_data)
        response = self._detail(product)
        response.status_code = status.HTTP_201_CREATED
        return response

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        product = self.get_object()
        serializer = ProductWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = save_product(request.user, data=serializer.validated_data, product=product)
        return self._detail(product)
