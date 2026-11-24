import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.catalog.models import Category, CategoryModerator

pytestmark = pytest.mark.django_db


def test_sibling_names_unique_case_insensitive():
    parent = Category.objects.create(name="Figurki i gaming")
    Category.objects.create(name="Figurki", parent=parent)
    with pytest.raises(IntegrityError):
        Category.objects.create(name="figurki", parent=parent)


def test_same_name_under_different_parents_allowed():
    first = Category.objects.create(name="Dom")
    second = Category.objects.create(name="Prezenty")
    Category.objects.create(name="Organizery", parent=first)
    Category.objects.create(name="Organizery", parent=second)
    assert Category.objects.filter(name="Organizery").count() == 2


def test_root_names_unique_case_insensitive():
    # NULL parents never collide in a plain unique index, hence the second, conditional constraint.
    Category.objects.create(name="Dom")
    with pytest.raises(IntegrityError):
        Category.objects.create(name="dom")


def test_parent_with_children_cannot_be_deleted():
    parent = Category.objects.create(name="Dom")
    Category.objects.create(name="Organizery", parent=parent)
    with pytest.raises(ProtectedError):
        parent.delete()


def test_children_related_name():
    parent = Category.objects.create(name="Dom")
    Category.objects.create(name="Organizery", parent=parent)
    Category.objects.create(name="Uchwyty", parent=parent)
    assert parent.children.count() == 2


def test_default_ordering_by_position_then_name():
    Category.objects.create(name="B", position=1)
    Category.objects.create(name="A", position=1)
    Category.objects.create(name="Z", position=0)
    assert [c.name for c in Category.objects.all()] == ["Z", "A", "B"]


def test_moderator_link_unique_pair(moderator):
    category = Category.objects.create(name="Dom")
    CategoryModerator.objects.create(category=category, moderator=moderator)
    with pytest.raises(IntegrityError):
        CategoryModerator.objects.create(category=category, moderator=moderator)
