import importlib

import pytest
from django.apps import apps

from apps.catalog.models import Category

pytestmark = pytest.mark.django_db

# The module name starts with a digit, so it cannot be imported with a plain import statement
migration = importlib.import_module("apps.catalog.migrations.0002_seed_categories")


def test_seed_creates_five_roots_and_two_subcategories():
    migration.seed(apps, None)

    roots = Category.objects.filter(parent__isnull=True)
    assert [root.name for root in roots] == [
        "Dom i organizacja",
        "Figurki i gaming",
        "Części zamienne",
        "Edukacja",
        "Prezenty",
    ]
    assert Category.objects.filter(parent__isnull=False).count() == 2
    assert Category.objects.get(name="Organizery").parent.name == "Dom i organizacja"


def test_seed_is_idempotent():
    migration.seed(apps, None)
    migration.seed(apps, None)

    assert Category.objects.count() == 7


def test_unseed_removes_seeded_categories_but_keeps_ones_with_extra_children():
    migration.seed(apps, None)
    home = Category.objects.get(name="Dom i organizacja")
    Category.objects.create(name="Moja podkategoria", parent=home)

    migration.unseed(apps, None)

    # "Organizery" (a seeded leaf) and the four untouched roots are gone;
    # the root that got a subcategory of its own stays, with that subcategory
    assert sorted(Category.objects.values_list("name", flat=True)) == [
        "Dom i organizacja",
        "Moja podkategoria",
    ]
