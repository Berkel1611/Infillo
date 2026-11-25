from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


def make_product(name: str = "Figurka smoka", **kwargs) -> Product:
    category = kwargs.pop("category", None) or Category.objects.create(name=f"Kat {name}")
    return Product.objects.create(name=name, category=category, **kwargs)


def make_variant(product: Product, **kwargs) -> ProductVariant:
    kwargs.setdefault("price", Decimal("49.00"))
    return ProductVariant.objects.create(product=product, **kwargs)


def test_price_must_be_positive():
    product = make_product()
    for price in (Decimal("0"), Decimal("-1.00")):
        with pytest.raises(IntegrityError), transaction.atomic():
            make_variant(product, price=price)
    assert product.variants.count() == 0


def test_stock_cannot_be_negative():
    product = make_product()
    with pytest.raises(IntegrityError), transaction.atomic():
        make_variant(product, stock=-1)


def test_duplicate_variant_combination_rejected():
    product = make_product()
    make_variant(product, color="czerwony", material="PLA", size="M")
    with pytest.raises(IntegrityError), transaction.atomic():
        make_variant(product, color="czerwony", material="PLA", size="M")

    # a different size, or the same combination on another product, is fine
    make_variant(product, color="czerwony", material="PLA", size="L")
    make_variant(make_product("Inny"), color="czerwony", material="PLA", size="M")


def test_variants_deleted_with_product():
    product = make_product()
    make_variant(product, size="S")
    make_variant(product, size="M")

    product.delete()

    assert ProductVariant.objects.count() == 0


def test_category_with_products_is_protected():
    product = make_product()
    with pytest.raises(ProtectedError):
        product.category.delete()


def test_created_by_set_null_when_user_deleted(regular_user):
    product = make_product(created_by=regular_user)

    regular_user.delete()

    product.refresh_from_db()
    assert product.created_by is None


def test_description_defaults_to_empty_document():
    product = make_product()
    product.refresh_from_db()
    assert product.description == {"type": "doc", "content": []}
    # every product gets its own copy of the default
    assert make_product("Drugi").description is not product.description


def test_defaults_and_reverse_names():
    product = make_product()
    variant = make_variant(product)

    assert product.is_published is False
    assert variant.stock == 0 and variant.made_to_order is False
    assert (variant.color, variant.material, variant.size) == ("", "", "")
    assert list(product.category.products.all()) == [product]
    assert list(product.variants.all()) == [variant]
    assert variant.price == Decimal("49.00")
