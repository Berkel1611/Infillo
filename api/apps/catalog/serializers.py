from rest_framework import serializers

from apps.catalog.models import Category


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
