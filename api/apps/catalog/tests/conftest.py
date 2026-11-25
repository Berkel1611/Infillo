import pytest

from apps.catalog.models import Category


@pytest.fixture(autouse=True)
def no_seeded_categories(db):
    """The test database is built from migrations, so the seed migration leaves example
    categories in it. Catalog tests count and compare categories, so start each one empty."""
    Category.objects.filter(parent__isnull=False).delete()
    Category.objects.all().delete()
