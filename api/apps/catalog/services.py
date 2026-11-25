from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.accounts.models import MODERATORS_GROUP, ROLE_ADMIN, ROLE_MODERATOR
from apps.catalog.models import (
    Category,
    CategoryModerator,
    Product,
    ProductVariant,
    empty_description,
)
from apps.catalog.rich_text import is_empty_description
from apps.core.exceptions import AppError

User = get_user_model()

MAX_CATEGORY_DEPTH = 3


@dataclass
class CategoryNode:
    id: int
    name: str
    parent_id: int | None
    children: list[CategoryNode] = field(default_factory=list)


def build_category_tree() -> list[CategoryNode]:
    """Builds a tree of categories from the database."""

    rows = Category.objects.values_list("id", "parent_id", "name")
    children_of: dict[int | None, list[tuple[int, str]]] = defaultdict(list)

    for id_, parent_id, name in rows:
        children_of[parent_id].append((id_, name))

    def build(parent_id: int | None) -> list[CategoryNode]:
        return [
            CategoryNode(id=id_, name=name, parent_id=parent_id, children=build(id_))
            for id_, name in children_of[parent_id]
        ]

    return build(None)  # Return the root nodes


def _load_parents() -> dict[int, int | None]:
    """One query: {category id: parent id}. All tree helpers work on this map in memory."""
    return dict(Category.objects.values_list("id", "parent_id"))


def _children_of(parent_of: dict[int, int | None]) -> dict[int | None, list[int]]:
    children_of: dict[int | None, list[int]] = defaultdict(list)
    for id_, parent_id in parent_of.items():
        children_of[parent_id].append(id_)
    return children_of


def _descendants(children_of: dict[int | None, list[int]], category_id: int) -> set[int]:
    """Iterative walk down the tree (a stack instead of recursion); excludes the node itself."""
    result: set[int] = set()
    stack = [category_id]
    while stack:
        for child_id in children_of[stack.pop()]:
            result.add(child_id)
            stack.append(child_id)
    return result


def _subtree_height(children_of: dict[int | None, list[int]], category_id: int) -> int:
    """Number of levels below the node: 0 for a leaf."""
    children = children_of[category_id]
    return 1 + max(_subtree_height(children_of, child) for child in children) if children else 0


def descendant_ids(category_id: int) -> set[int]:
    """All categories below `category_id` (children, grandchildren...), without itself."""
    return _descendants(_children_of(_load_parents()), category_id)


def validate_category_placement(category_id: int | None, parent_id: int | None) -> None:
    """Checks that putting a category under `parent_id` keeps the tree valid.

    `category_id` is None when creating a new category. The cycle is checked before the depth:
    moving a node under its own descendant would otherwise be reported as "too deep".
    """
    if parent_id is None:  # a root is always fine; its subtree already fits
        return

    parent_of = _load_parents()
    children_of = _children_of(parent_of)

    if category_id is not None and (
        parent_id == category_id or parent_id in _descendants(children_of, category_id)
    ):
        raise AppError("CATEGORY_CYCLE", 400)

    # Depth of the new parent = number of nodes on the path up to the root (root = 1)
    parent_depth = 0
    current: int | None = parent_id
    while current is not None:
        parent_depth += 1
        current = parent_of[current]

    moved_height = 0 if category_id is None else _subtree_height(children_of, category_id)
    if parent_depth + 1 + moved_height > MAX_CATEGORY_DEPTH:
        raise AppError("CATEGORY_TOO_DEEP", 400)


def _name_taken(name: str, parent_id: int | None, exclude_pk: int | None = None) -> bool:
    qs = Category.objects.filter(name__iexact=name.strip(), parent_id=parent_id)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def create_category(name: str, parent_id: int | None) -> Category:
    name = name.strip()
    validate_category_placement(None, parent_id)
    if _name_taken(name, parent_id):
        raise AppError("CATEGORY_NAME_TAKEN", 409)
    try:
        with transaction.atomic():
            return Category.objects.create(name=name, parent_id=parent_id)
    except IntegrityError:
        raise AppError("CATEGORY_NAME_TAKEN", 409) from None


def update_category(category: Category, changes: dict[str, Any]) -> Category:
    # A missing key means "unchanged"; parent_id=None is a real value (move to the root)
    new_name = changes["name"].strip() if "name" in changes else category.name
    new_parent_id = changes["parent_id"] if "parent_id" in changes else category.parent_id

    if new_parent_id != category.parent_id:
        validate_category_placement(category.id, new_parent_id)
    # Uniqueness is about the pair (name, parent), so it is checked when either one changes
    if _name_taken(new_name, new_parent_id, exclude_pk=category.id):
        raise AppError("CATEGORY_NAME_TAKEN", 409)

    # Assign only after every check passed, so a rejected change leaves the object untouched
    category.name = new_name
    category.parent_id = new_parent_id
    try:
        with transaction.atomic():  # savepoint: a lost race must not poison the transaction
            category.save()
    except IntegrityError:
        raise AppError("CATEGORY_NAME_TAKEN", 409) from None
    return category


def delete_category(category: Category) -> None:
    try:
        with transaction.atomic():
            category.delete()
    except ProtectedError:
        raise AppError("CATEGORY_NOT_EMPTY", 409) from None


def _moderators():
    """Accounts that currently are moderators: in the group and not a superuser (= admin).
    Assignment rows of users who lost the role stay in the database, but never count."""
    return User.objects.filter(groups__name=MODERATORS_GROUP, is_superuser=False)


def category_moderators(category: Category) -> list[User]:
    assigned = CategoryModerator.objects.filter(category=category).values("moderator_id")
    return list(_moderators().filter(pk__in=assigned).order_by("username"))


def set_category_moderators(category: Category, moderator_ids: list[int]) -> list[User]:
    """Replaces the whole set of moderators of a category; all ids must be current moderators."""
    wanted = set(moderator_ids)
    valid = set(_moderators().filter(pk__in=wanted).values_list("pk", flat=True))
    if valid != wanted:
        raise AppError("USER_NOT_MODERATOR", 400)

    with transaction.atomic():  # either the whole new set is saved or nothing changes
        CategoryModerator.objects.filter(category=category).exclude(
            moderator_id__in=wanted
        ).delete()
        CategoryModerator.objects.bulk_create(
            [CategoryModerator(category=category, moderator_id=pk) for pk in wanted],
            ignore_conflicts=True,  # rows that already exist stay as they are
        )
    return category_moderators(category)


def managed_category_ids(user) -> set[int]:
    """Categories whose products the user may manage: admin = all, moderator = assigned
    categories and everything below them, anyone else = nothing."""
    if not user.is_authenticated:
        return set()
    if user.role == ROLE_ADMIN:
        return set(Category.objects.values_list("pk", flat=True))
    if user.role != ROLE_MODERATOR:
        return set()

    children_of = _children_of(_load_parents())
    assigned = set(
        CategoryModerator.objects.filter(moderator=user).values_list("category_id", flat=True)
    )
    scope = set(assigned)
    for category_id in assigned:
        scope |= _descendants(children_of, category_id)
    return scope


class Availability(StrEnum):
    """Availability codes exposed by the API; the frontend turns them into Polish labels."""

    AVAILABLE = "AVAILABLE"
    MADE_TO_ORDER = "MADE_TO_ORDER"
    OUT_OF_STOCK = "OUT_OF_STOCK"


# Best first: a product shows the best status among its variants
_AVAILABILITY_RANK = (Availability.AVAILABLE, Availability.MADE_TO_ORDER, Availability.OUT_OF_STOCK)


def variant_availability(stock: int, made_to_order: bool) -> Availability:
    """Pure function (no model property): the cart (stage 5) reuses it on its own data."""
    if stock > 0:
        return Availability.AVAILABLE
    if made_to_order:
        return Availability.MADE_TO_ORDER
    return Availability.OUT_OF_STOCK


def product_availability(variants: Iterable[ProductVariant]) -> Availability:
    statuses = {variant_availability(v.stock, v.made_to_order) for v in variants}
    return next((s for s in _AVAILABILITY_RANK if s in statuses), Availability.OUT_OF_STOCK)


VARIANT_FIELDS = ("color", "material", "size", "price", "stock", "made_to_order")
PRODUCT_FIELDS = ("name", "description", "category_id", "is_published")


COMBINATION_FIELDS = ("color", "material", "size")


def _sync_variants(product: Product, items: list[dict[str, Any]]) -> None:
    """Makes the variants of `product` equal to `items`: with id -> update, without -> create,
    missing from the list -> delete."""
    existing = {variant.id: variant for variant in product.variants.all()}
    kept_ids = {item["id"] for item in items if item.get("id") is not None}
    if not kept_ids <= existing.keys():  # an id of another product (or of no product at all)
        raise AppError("VARIANT_NOT_FOUND", 400)

    # The list is the final state, so its combinations must be distinct. A kept variant keeps
    # the values the request does not mention, which is why this is checked here and not only
    # in the serializer (it sees just what the request says).
    def combination(item: dict[str, Any]) -> tuple[str, ...]:
        current = existing.get(item.get("id"))
        return tuple(
            item[name] if name in item else getattr(current, name, "")
            for name in COMBINATION_FIELDS
        )

    combinations = [combination(item) for item in items]
    if len(set(combinations)) != len(combinations):
        raise AppError("DUPLICATE_VARIANT", 400)

    # Deleting first: a variant can be replaced by one with the same combination in one request
    product.variants.exclude(id__in=kept_ids).delete()

    updates = [
        (existing[item["id"]], {name: item[name] for name in VARIANT_FIELDS if name in item})
        for item in items
        if item.get("id") is not None
    ]
    # Variants may trade combinations (S <-> M). Saved one by one, the first save would clash
    # with the other variant on the unique constraint although the final state is valid, so the
    # variants that change their combination are first parked on a unique placeholder size.
    for variant, fields in updates:
        if any(
            name in fields and fields[name] != getattr(variant, name) for name in COMBINATION_FIELDS
        ):
            variant.size = f"~{variant.pk}"
            variant.save(update_fields=["size"])
    for variant, fields in updates:
        for name, value in fields.items():
            setattr(variant, name, value)
        variant.save()

    for item in items:
        if item.get("id") is None:
            ProductVariant.objects.create(
                product=product, **{name: item[name] for name in VARIANT_FIELDS if name in item}
            )


def save_product(user, *, data: dict[str, Any], product: Product | None = None) -> Product:
    """Creates a product (`product=None`) or applies `data` to it; a missing key means
    "unchanged", `variants` present means "replace the whole list".

    The scope check lives here, not in the view: both the product's current category and
    the target category must be managed by `user`. The description is validated by the
    serializer (rich_text.validate_description); this function only checks publishing rules.
    """
    managed = managed_category_ids(user)
    if product is not None and product.category_id not in managed:
        raise AppError("CATEGORY_NOT_MANAGED", 403)
    category_id = data.get("category_id", product.category_id if product else None)
    if category_id not in managed:
        raise AppError("CATEGORY_NOT_MANAGED", 403)

    # Publishing rules apply to the state the product will have after this save
    variants = data.get("variants")
    is_published = data.get("is_published", product.is_published if product else False)
    description = data.get("description", product.description if product else empty_description())
    if is_published:
        if variants is not None:
            variant_count = len(variants)
        else:
            variant_count = product.variants.count() if product else 0
        if variant_count == 0:
            raise AppError("PUBLISH_REQUIRES_VARIANT", 400)
        if is_empty_description(description):
            raise AppError("PUBLISH_REQUIRES_DESCRIPTION", 400)

    with transaction.atomic():  # the product and its variants are saved together or not at all
        if product is None:
            product = Product(created_by=user)
        for name in PRODUCT_FIELDS:
            if name in data:
                setattr(product, name, data[name])
        product.save()
        if variants is not None:
            _sync_variants(product, variants)
    return product


def category_path(category_id: int) -> list[dict[str, Any]]:
    """Ancestors of a category from the root down to the category itself: [{id, name}, ...]."""
    rows = {
        id_: (parent_id, name)
        for id_, parent_id, name in Category.objects.values_list("id", "parent_id", "name")
    }
    path: list[dict[str, Any]] = []
    current: int | None = category_id
    while current is not None:
        parent_id, name = rows[current]
        path.append({"id": current, "name": name})
        current = parent_id
    return path[::-1]
