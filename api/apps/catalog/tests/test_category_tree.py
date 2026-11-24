import pytest

from apps.catalog.models import Category
from apps.catalog.services import (
    MAX_CATEGORY_DEPTH,
    CategoryNode,
    build_category_tree,
    descendant_ids,
    validate_category_placement,
)
from apps.core.exceptions import AppError

pytestmark = pytest.mark.django_db


def make(name: str, parent: Category | None = None, position: int = 0) -> Category:
    return Category.objects.create(name=name, parent=parent, position=position)


def chain(depth: int) -> list[Category]:
    """Creates a straight line root -> ... with `depth` levels and returns it top-down."""
    nodes: list[Category] = []
    for level in range(depth):
        nodes.append(make(f"level {level + 1}", nodes[-1] if nodes else None))
    return nodes


def test_max_depth_is_three():
    assert MAX_CATEGORY_DEPTH == 3


def test_tree_nests_children_in_order():
    home = make("Dom", position=1)
    figures = make("Figurki", position=0)
    make("Uchwyty", home, position=1)
    make("Organizery", home, position=0)

    tree = build_category_tree()

    assert all(isinstance(node, CategoryNode) for node in tree)
    assert [node.name for node in tree] == ["Figurki", "Dom"]
    assert tree[0].id == figures.id and tree[0].parent_id is None and tree[0].children == []
    assert [child.name for child in tree[1].children] == ["Organizery", "Uchwyty"]
    assert all(child.parent_id == home.id for child in tree[1].children)


def test_tree_uses_single_query(django_assert_num_queries):
    root = make("Dom")
    middle = make("Organizery", root)
    make("Pudelka", middle)
    make("Figurki")

    with django_assert_num_queries(1):
        tree = build_category_tree()

    assert len(tree) == 2


def test_descendant_ids_of_root_leaf_and_middle():
    root, middle, leaf = chain(3)
    other = make("Inne")

    assert descendant_ids(root.id) == {middle.id, leaf.id}
    assert descendant_ids(middle.id) == {leaf.id}
    assert descendant_ids(leaf.id) == set()
    assert other.id not in descendant_ids(root.id)


def test_depth_three_allowed():
    _root, middle = chain(2)
    validate_category_placement(None, middle.id)  # a new category on level 3


def test_depth_four_rejected():
    *_, leaf = chain(3)
    with pytest.raises(AppError) as exc:
        validate_category_placement(None, leaf.id)  # would be level 4
    assert exc.value.error_code == "CATEGORY_TOO_DEEP"


def test_creating_root_is_always_allowed():
    validate_category_placement(None, None)


def test_move_counts_subtree_height():
    # "moved" has one child (2 levels); under a level-2 parent it would end up on level 4
    moved = make("Moved")
    make("Moved child", moved)
    _root, level2 = chain(2)

    with pytest.raises(AppError) as exc:
        validate_category_placement(moved.id, level2.id)
    assert exc.value.error_code == "CATEGORY_TOO_DEEP"


def test_move_subtree_that_fits_is_allowed():
    moved = make("Moved")
    make("Moved child", moved)
    root = make("Root")  # parent on level 1 -> subtree occupies levels 2-3

    validate_category_placement(moved.id, root.id)


def test_parent_is_self_rejected():
    category = make("Dom")
    with pytest.raises(AppError) as exc:
        validate_category_placement(category.id, category.id)
    assert exc.value.error_code == "CATEGORY_CYCLE"


def test_parent_is_descendant_rejected():
    # The move would also be too deep, but the cycle has to be reported first
    root, _middle, leaf = chain(3)
    with pytest.raises(AppError) as exc:
        validate_category_placement(root.id, leaf.id)
    assert exc.value.error_code == "CATEGORY_CYCLE"


def test_move_to_root_allowed():
    *_, leaf = chain(3)
    validate_category_placement(leaf.id, None)
