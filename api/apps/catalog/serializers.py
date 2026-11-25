from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from apps.catalog import rich_text
from apps.catalog.models import Category
from apps.catalog.services import category_path, product_availability, variant_availability


class CategoryNodeSerializer(serializers.Serializer):
    """Output of GET /categories: a recursive tree built from CategoryNode dataclasses."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    children = serializers.SerializerMethodField()

    def get_children(self, node) -> list[dict]:
        # The serializer calls itself for the subtree; depth is capped at 3 by the service
        return CategoryNodeSerializer(node.children, many=True).data


class CategorySerializer(serializers.Serializer):
    """Output of POST / PATCH: one category without children."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    parent_id = serializers.IntegerField(allow_null=True)


class CategoryWriteSerializer(serializers.Serializer):
    """Input of POST / PATCH. With partial=True a missing key stays missing in validated_data,
    which the service reads as "unchanged"; parent_id=null means "move to the root"."""

    # CharField trims whitespace and rejects blank values by default
    name = serializers.CharField(max_length=100)
    parent_id = serializers.IntegerField(allow_null=True, required=False)

    def validate_parent_id(self, value: int | None) -> int | None:
        if value is not None and not Category.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Category does not exist.", code="does_not_exist")
        return value


class ModeratorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class ModeratorAssignSerializer(serializers.Serializer):
    """Input of PUT /categories/{id}/moderators: the full new set of moderators."""

    moderator_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


# --- products: input ---

VARIANT_COMBINATION_FIELDS = ("color", "material", "size")
# stock is a 4-byte integer column: a bigger number would be a database error (500)
MAX_STOCK = 2_147_483_647


class VariantWriteSerializer(serializers.Serializer):
    """One variant of the `variants` list. With PATCH (partial=True on the parent) DRF skips
    "required" checks in nested serializers too, so the price of a new variant is checked in
    validate()."""

    id = serializers.IntegerField(required=False)
    color = serializers.CharField(max_length=50, required=False, allow_blank=True)
    material = serializers.CharField(max_length=50, required=False, allow_blank=True)
    size = serializers.CharField(max_length=50, required=False, allow_blank=True)
    price = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal("0.01"), required=False
    )
    stock = serializers.IntegerField(min_value=0, max_value=MAX_STOCK, required=False)
    made_to_order = serializers.BooleanField(required=False)

    def validate(self, attrs: dict) -> dict:
        if "id" not in attrs and "price" not in attrs:
            raise serializers.ValidationError(
                {"price": [ErrorDetail("This field is required.", code="required")]}
            )
        return attrs


class ProductWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.JSONField(required=False)
    category_id = serializers.IntegerField()
    is_published = serializers.BooleanField(required=False)
    variants = VariantWriteSerializer(many=True, required=False)

    def validate_description(self, value):
        # The allowlist lives in rich_text.py; its error code becomes the "type" of the field error
        try:
            rich_text.validate_description(value)
        except rich_text.InvalidDescription as exc:
            raise serializers.ValidationError("Invalid description.", code=exc.code) from None
        return value

    def validate_category_id(self, value: int) -> int:
        if not Category.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Category does not exist.", code="does_not_exist")
        return value

    def validate_variants(self, items: list[dict]) -> list[dict]:
        ids = [item["id"] for item in items if "id" in item]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Variant sent twice.", code="duplicate_variant")
        # Compare combinations only where they are fully known: a new variant (missing fields
        # default to "") or an existing one that states all three
        combinations = [
            tuple(item.get(name, "") for name in VARIANT_COMBINATION_FIELDS)
            for item in items
            if "id" not in item or all(name in item for name in VARIANT_COMBINATION_FIELDS)
        ]
        if len(combinations) != len(set(combinations)):
            raise serializers.ValidationError(
                "Two variants with the same color, material and size.", code="duplicate_variant"
            )
        return items


class ProductListQuerySerializer(serializers.Serializer):
    """Query string of GET /products and /products/managed (?category=&search=)."""

    category = serializers.IntegerField(required=False)
    search = serializers.CharField(max_length=100, required=False, allow_blank=True)


# --- products: output ---


def _money(value: Decimal | None) -> str | None:
    """Prices travel as text ("49.00"): a JSON number would go through float."""
    return None if value is None else f"{value:.2f}"


class VariantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    color = serializers.CharField()
    material = serializers.CharField()
    size = serializers.CharField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    stock = serializers.IntegerField()
    made_to_order = serializers.BooleanField()
    availability = serializers.SerializerMethodField()

    def get_availability(self, variant) -> str:
        return variant_availability(variant.stock, variant.made_to_order).value


class CategoryRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class ProductRowSerializer(serializers.Serializer):
    """A row of a product list. `price_from` is annotated by the view (one query for the page)
    and the variants come from prefetch_related, so a page needs no per-row queries."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    category = CategoryRefSerializer()
    price_from = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    availability = serializers.SerializerMethodField()

    def get_availability(self, product) -> str:
        return product_availability(product.variants.all()).value


class ManagedProductRowSerializer(ProductRowSerializer):
    is_published = serializers.BooleanField()


class ProductDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.JSONField()
    is_published = serializers.BooleanField()
    category = CategoryRefSerializer()
    category_path = serializers.SerializerMethodField()
    price_from = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    def get_category_path(self, product) -> list[dict]:
        return category_path(product.category_id)

    def get_price_from(self, product) -> str | None:
        return _money(min((v.price for v in product.variants.all()), default=None))

    def get_availability(self, product) -> str:
        return product_availability(product.variants.all()).value

    def get_variants(self, product) -> list[dict]:
        return VariantSerializer(product.variants.all(), many=True).data
