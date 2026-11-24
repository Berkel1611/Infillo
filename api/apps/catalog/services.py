from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from apps.catalog.models import Category
from apps.core.exceptions import AppError

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
