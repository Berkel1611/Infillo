from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.db import IntegrityError

from apps.accounts.models import MODERATORS_GROUP
from apps.catalog.models import Category, CategoryModerator, Product, ProductVariant
from apps.catalog.services import save_product
from apps.core.exceptions import AppError

pytestmark = pytest.mark.django_db

DESCRIPTION = {
    "type": "doc",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Opis"}]}],
}


def make(name: str, parent: Category | None = None) -> Category:
    return Category.objects.create(name=name, parent=parent)


def variant_data(**kwargs) -> dict:
    return {"color": "czerwony", "price": Decimal("49.00"), "stock": 2, **kwargs}


def product_data(category: Category, **kwargs) -> dict:
    return {"name": "Figurka smoka", "category_id": category.id, **kwargs}


def assign(category: Category, user) -> None:
    CategoryModerator.objects.create(category=category, moderator=user)


def error_of(callable_, *args, **kwargs) -> AppError:
    with pytest.raises(AppError) as exc:
        callable_(*args, **kwargs)
    return exc.value


@pytest.fixture
def published_product(administrator):
    category = make("Dom")
    return save_product(
        administrator,
        data=product_data(
            category,
            description=DESCRIPTION,
            is_published=True,
            variants=[variant_data(size="S"), variant_data(size="M")],
        ),
    )


# --- scope ---


def test_moderator_creates_in_scope_and_descendant(moderator):
    root = make("Dom")
    child = make("Organizery", root)
    assign(root, moderator)

    in_root = save_product(moderator, data=product_data(root))
    in_child = save_product(moderator, data=product_data(child, name="Inny"))

    assert in_root.category_id == root.id and in_child.category_id == child.id
    assert Product.objects.count() == 2


def test_moderator_outside_scope_403(moderator):
    assigned, other = make("Dom"), make("Figurki")
    assign(assigned, moderator)

    error = error_of(save_product, moderator, data=product_data(other))

    assert (error.error_code, error.status_code) == ("CATEGORY_NOT_MANAGED", 403)
    assert Product.objects.count() == 0


def test_moved_to_unmanaged_category_403(moderator):
    assigned, other = make("Dom"), make("Figurki")
    assign(assigned, moderator)
    product = save_product(moderator, data=product_data(assigned))

    error = error_of(save_product, moderator, data={"category_id": other.id}, product=product)

    assert error.error_code == "CATEGORY_NOT_MANAGED"
    product.refresh_from_db()
    assert product.category_id == assigned.id


def test_product_in_unmanaged_category_cannot_be_edited(moderator, administrator):
    other = make("Figurki")
    assigned = make("Dom")
    assign(assigned, moderator)
    foreign = save_product(administrator, data=product_data(other))

    # even without moving it anywhere (the old category is out of scope)
    error = error_of(save_product, moderator, data={"name": "Przejęty"}, product=foreign)
    assert error.error_code == "CATEGORY_NOT_MANAGED"
    # and moving it into the moderator's own category does not help either
    error = error_of(save_product, moderator, data={"category_id": assigned.id}, product=foreign)
    assert error.error_code == "CATEGORY_NOT_MANAGED"
    foreign.refresh_from_db()
    assert foreign.name == "Figurka smoka" and foreign.category_id == other.id


def test_admin_anywhere(administrator):
    one, two = make("Dom"), make("Figurki")

    save_product(administrator, data=product_data(one))
    save_product(administrator, data=product_data(two, name="Inny"))

    assert Product.objects.count() == 2


def test_unknown_category_is_not_managed_even_for_admin(administrator):
    error = error_of(save_product, administrator, data={"name": "X", "category_id": 999_999})
    assert error.error_code == "CATEGORY_NOT_MANAGED"


def test_moderator_who_lost_role_denied(moderator):
    # Review Focus 3: the assignment row stays, but it must not grant anything
    category = make("Dom")
    assign(category, moderator)
    moderator.groups.remove(Group.objects.get(name=MODERATORS_GROUP))

    error = error_of(save_product, moderator, data=product_data(category))

    assert error.error_code == "CATEGORY_NOT_MANAGED"


def test_created_by_set_on_create_and_kept_on_update(moderator, administrator):
    category = make("Dom")
    assign(category, moderator)
    product = save_product(moderator, data=product_data(category))
    assert product.created_by == moderator

    save_product(administrator, data={"name": "Zmieniona"}, product=product)

    product.refresh_from_db()
    assert product.created_by == moderator and product.name == "Zmieniona"


# --- publishing ---


def test_publish_needs_variant_and_description(administrator):
    category = make("Dom")

    no_variant = error_of(
        save_product,
        administrator,
        data=product_data(category, description=DESCRIPTION, is_published=True),
    )
    no_description = error_of(
        save_product,
        administrator,
        data=product_data(category, is_published=True, variants=[variant_data()]),
    )

    assert (no_variant.error_code, no_variant.status_code) == ("PUBLISH_REQUIRES_VARIANT", 400)
    assert no_description.error_code == "PUBLISH_REQUIRES_DESCRIPTION"
    assert Product.objects.count() == 0


def test_draft_needs_neither_variant_nor_description(administrator):
    product = save_product(administrator, data=product_data(make("Dom")))
    assert product.is_published is False


def test_publish_rules_apply_to_the_resulting_state(administrator, published_product):
    # removing every variant of a published product would leave it unsellable
    error = error_of(save_product, administrator, data={"variants": []}, product=published_product)
    assert error.error_code == "PUBLISH_REQUIRES_VARIANT"
    assert published_product.variants.count() == 2

    # an emptied description as well
    empty = {"type": "doc", "content": [{"type": "paragraph"}]}
    error = error_of(
        save_product, administrator, data={"description": empty}, product=published_product
    )
    assert error.error_code == "PUBLISH_REQUIRES_DESCRIPTION"

    # unpublishing is always allowed
    save_product(
        administrator, data={"is_published": False, "variants": []}, product=published_product
    )
    published_product.refresh_from_db()
    assert published_product.is_published is False and published_product.variants.count() == 0


def test_publish_existing_draft_uses_stored_variants_and_description(administrator):
    category = make("Dom")
    draft = save_product(
        administrator,
        data=product_data(category, description=DESCRIPTION, variants=[variant_data()]),
    )

    save_product(administrator, data={"is_published": True}, product=draft)

    draft.refresh_from_db()
    assert draft.is_published is True


# --- variants ---


def test_patch_without_variants_keeps_them(administrator, published_product):
    save_product(administrator, data={"name": "Nowa nazwa"}, product=published_product)

    assert published_product.variants.count() == 2
    published_product.refresh_from_db()
    assert published_product.name == "Nowa nazwa"


def test_variants_replaced_by_id(administrator, published_product):
    keep, drop = published_product.variants.order_by("id")

    save_product(
        administrator,
        data={
            "variants": [
                {"id": keep.id, "price": Decimal("59.90"), "stock": 7},  # update, other fields stay
                variant_data(size="XL"),  # no id -> new variant; `drop` is missing -> deleted
            ]
        },
        product=published_product,
    )

    variants = list(published_product.variants.order_by("id"))
    assert [v.size for v in variants] == ["S", "XL"]
    assert not ProductVariant.objects.filter(pk=drop.pk).exists()
    updated = variants[0]
    assert updated.pk == keep.pk
    assert (updated.price, updated.stock, updated.color) == (Decimal("59.90"), 7, "czerwony")


def test_variant_combination_can_be_reused_after_replacing(administrator, published_product):
    old_small, medium = published_product.variants.order_by("id")  # sizes "S" and "M"

    # "S" is left out and a new "S" is sent in one request: removed rows go first,
    # so the new row does not clash with the old one on the unique combination
    save_product(
        administrator,
        data={"variants": [{"id": medium.id}, variant_data(size="S", stock=9)]},
        product=published_product,
    )

    variants = {v.size: v for v in published_product.variants.all()}
    assert sorted(variants) == ["M", "S"]
    assert variants["S"].pk != old_small.pk and variants["S"].stock == 9


def test_foreign_variant_id_rejected(administrator, published_product):
    other = save_product(
        administrator, data=product_data(make("Figurki"), variants=[variant_data()])
    )
    foreign_id = other.variants.get().id

    error = error_of(
        save_product,
        administrator,
        data={"variants": [{"id": foreign_id}]},
        product=published_product,
    )

    assert (error.error_code, error.status_code) == ("VARIANT_NOT_FOUND", 400)
    assert other.variants.count() == 1 and published_product.variants.count() == 2


def test_new_product_cannot_reference_variant_ids(administrator):
    error = error_of(
        save_product,
        administrator,
        data=product_data(make("Dom"), variants=[variant_data(id=1)]),
    )
    assert error.error_code == "VARIANT_NOT_FOUND"
    assert Product.objects.count() == 0


def test_failure_rolls_back_whole_save(administrator):
    category = make("Dom")

    with pytest.raises(IntegrityError):  # the database rejects price 0 (CheckConstraint)
        save_product(
            administrator,
            data=product_data(
                category,
                variants=[variant_data(size="S"), variant_data(size="M", price=Decimal("0"))],
            ),
        )

    # neither the product nor the first, valid variant was saved
    assert Product.objects.count() == 0
    assert ProductVariant.objects.count() == 0


def test_failed_update_leaves_stored_product_untouched(administrator, published_product):
    keep = published_product.variants.order_by("id").first()

    with pytest.raises(IntegrityError):
        save_product(
            administrator,
            data={
                "name": "Nie zapisana",
                "variants": [
                    {"id": keep.id, "stock": 99},
                    variant_data(size="XL", price=Decimal("0")),
                ],
            },
            product=published_product,
        )

    stored = Product.objects.get(pk=published_product.pk)
    assert stored.name == "Figurka smoka"
    assert ProductVariant.objects.get(pk=keep.pk).stock == 2
    assert stored.variants.count() == 2
