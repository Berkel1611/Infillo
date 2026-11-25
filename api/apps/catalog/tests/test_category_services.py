import pytest

from apps.catalog.models import Category, Product
from apps.catalog.services import create_category, delete_category, update_category
from apps.core.exceptions import AppError

pytestmark = pytest.mark.django_db


def make(name: str, parent: Category | None = None) -> Category:
    return Category.objects.create(name=name, parent=parent)


def error_code(exc_info) -> str:
    return exc_info.value.error_code


def test_create_root_and_child():
    root = create_category("Dom", None)
    child = create_category("Organizery", root.id)

    assert root.parent_id is None
    assert child.parent_id == root.id
    assert Category.objects.count() == 2


def test_create_trims_name():
    assert create_category("  Dom  ", None).name == "Dom"


@pytest.mark.parametrize("name", ["Dom", "dom", "DOM"])
def test_duplicate_root_name_conflicts(name):
    create_category("Dom", None)
    with pytest.raises(AppError) as exc:
        create_category(name, None)
    assert error_code(exc) == "CATEGORY_NAME_TAKEN"
    assert exc.value.status_code == 409


def test_duplicate_name_in_siblings_conflicts_and_database_stays_usable():
    root = create_category("Dom", None)
    create_category("Organizery", root.id)

    with pytest.raises(AppError) as exc:
        create_category("organizery", root.id)
    assert error_code(exc) == "CATEGORY_NAME_TAKEN"

    # A failed insert must not poison the surrounding transaction
    assert Category.objects.count() == 2


def test_same_name_other_parent_ok():
    first = create_category("Dom", None)
    second = create_category("Prezenty", None)
    create_category("Organizery", first.id)
    create_category("Organizery", second.id)

    assert Category.objects.filter(name="Organizery").count() == 2


def test_create_validates_placement():
    level1 = create_category("L1", None)
    level2 = create_category("L2", level1.id)
    level3 = create_category("L3", level2.id)

    with pytest.raises(AppError) as exc:
        create_category("L4", level3.id)
    assert error_code(exc) == "CATEGORY_TOO_DEEP"


def test_update_renames_and_moves():
    home = make("Dom")
    gifts = make("Prezenty")
    category = make("Organizery", home)

    updated = update_category(category, {"name": "  Uchwyty ", "parent_id": gifts.id})

    category.refresh_from_db()
    assert updated.pk == category.pk
    assert category.name == "Uchwyty"
    assert category.parent_id == gifts.id


def test_update_missing_key_means_no_change_and_none_parent_moves_to_root():
    home = make("Dom")
    category = make("Organizery", home)

    update_category(category, {"name": "Pudelka"})
    category.refresh_from_db()
    assert (category.name, category.parent_id) == ("Pudelka", home.id)

    update_category(category, {"parent_id": None})
    category.refresh_from_db()
    assert (category.name, category.parent_id) == ("Pudelka", None)


def test_update_can_change_only_letter_case_of_own_name():
    category = make("dom")
    update_category(category, {"name": "Dom"})
    category.refresh_from_db()
    assert category.name == "Dom"


def test_update_name_conflict_with_sibling():
    home = make("Dom")
    make("Organizery", home)
    category = make("Uchwyty", home)

    with pytest.raises(AppError) as exc:
        update_category(category, {"name": "ORGANIZERY"})
    assert error_code(exc) == "CATEGORY_NAME_TAKEN"


def test_update_move_to_root_conflicts_with_existing_root_name():
    make("Organizery")
    home = make("Dom")
    category = make("organizery", home)

    with pytest.raises(AppError) as exc:
        update_category(category, {"parent_id": None})
    assert error_code(exc) == "CATEGORY_NAME_TAKEN"


def test_update_validates_placement_cycle_and_depth():
    root = make("L1")
    middle = make("L2", root)
    leaf = make("L3", middle)

    with pytest.raises(AppError) as cycle:
        update_category(root, {"parent_id": leaf.id})
    assert error_code(cycle) == "CATEGORY_CYCLE"

    other = make("Inne")
    make("Inne dziecko", other)
    with pytest.raises(AppError) as deep:
        update_category(other, {"parent_id": middle.id})
    assert error_code(deep) == "CATEGORY_TOO_DEEP"


def test_delete_empty_category():
    category = make("Dom")
    delete_category(category)
    assert not Category.objects.filter(pk=category.pk).exists()


def test_delete_with_children_is_conflict():
    parent = make("Dom")
    make("Organizery", parent)

    with pytest.raises(AppError) as exc:
        delete_category(parent)
    assert error_code(exc) == "CATEGORY_NOT_EMPTY"
    assert exc.value.status_code == 409
    assert Category.objects.filter(pk=parent.pk).exists()


def test_delete_with_product_is_conflict():
    category = make("Dom")
    Product.objects.create(name="Figurka", category=category)

    with pytest.raises(AppError) as exc:
        delete_category(category)
    assert exc.value.error_code == "CATEGORY_NOT_EMPTY"
    assert Category.objects.filter(pk=category.pk).exists()
