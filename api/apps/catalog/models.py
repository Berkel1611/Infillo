from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class Category(models.Model):
    """A product category."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "parent",
                name="unique_category_name_with_parent",
                condition=models.Q(parent__isnull=False),
            ),
            models.UniqueConstraint(
                Lower("name"), name="unique_category_name", condition=models.Q(parent__isnull=True)
            ),
        ]

    def __str__(self):
        return self.name


class CategoryModerator(models.Model):
    """A user who moderates a category."""

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="moderator_links")
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "moderator"], name="unique_category_moderator"
            )
        ]

    def __str__(self):
        return f"{self.moderator} moderates {self.category}"


def empty_description() -> dict:
    """Default of Product.description. A function, so each product gets its own dict
    (a shared mutable default would leak changes between instances)."""
    return {"type": "doc", "content": []}


class Product(models.Model):
    """A printed item. The description is a TipTap document, validated in rich_text.py."""

    name = models.CharField(max_length=200)
    description = models.JSONField(default=empty_description)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """One purchasable variant: price in PLN, stock and the "made to order" flag."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    made_to_order = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name="variant_price_positive"),
            models.UniqueConstraint(
                fields=["product", "color", "material", "size"], name="unique_product_variant"
            ),
        ]

    def __str__(self):
        label = " / ".join(part for part in (self.color, self.material, self.size) if part)
        return f"{self.product} ({label or 'default'})"
