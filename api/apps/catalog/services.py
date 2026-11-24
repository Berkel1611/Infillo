from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.accounts.models import MODERATORS_GROUP, ROLE_ADMIN, ROLE_MODERATOR
from apps.catalog.models import Category, CategoryModerator
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
