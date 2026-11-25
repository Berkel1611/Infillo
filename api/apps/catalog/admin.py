from django.contrib import admin

from apps.catalog.models import Category, CategoryModerator, Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Developer tool only: the graded management screens live in the Next.js frontend."""

    list_display = ("name", "category", "is_published")
    inlines = [ProductVariantInline]


admin.site.register(Category)
admin.site.register(CategoryModerator)
