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
