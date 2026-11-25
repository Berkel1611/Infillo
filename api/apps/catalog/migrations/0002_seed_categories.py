from django.db import migrations

# Example categories from the project concept: (root, [subcategories])
SEED = [
    ("Dom i organizacja", ["Organizery"]),
    ("Figurki i gaming", ["Akcesoria do gier planszowych"]),
    ("Części zamienne", []),
    ("Edukacja", []),
    ("Prezenty", []),
]


def seed(apps, schema_editor):
    """Idempotent: get_or_create, so running it again never duplicates anything."""
    # Historical model: the schema as it was at this migration, not the current Category class
    Category = apps.get_model("catalog", "Category")
    for position, (root_name, children) in enumerate(SEED):
        root, _ = Category.objects.get_or_create(
            name=root_name, parent=None, defaults={"position": position}
        )
        for child_position, child_name in enumerate(children):
            Category.objects.get_or_create(
                name=child_name, parent=root, defaults={"position": child_position}
            )


def unseed(apps, schema_editor):
    """Removes seeded categories that are still leaves (children first, then emptied roots).
    Categories that gained subcategories of their own stay: PROTECT would refuse anyway."""
    Category = apps.get_model("catalog", "Category")
    for root_name, children in SEED:
        for child_name in children:
            Category.objects.filter(name=child_name, children__isnull=True).delete()
        Category.objects.filter(name=root_name, parent=None, children__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_category_models"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
