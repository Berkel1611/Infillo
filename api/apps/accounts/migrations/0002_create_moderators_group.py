from django.db import migrations

# Same value as MODERATORS_GROUP in models.py. Migrations keep their own copy on purpose:
# they must keep working after the model code changes.
MODERATORS_GROUP = "moderators"


def create_moderators_group(apps, schema_editor):
    # Historical model: the state of Group at this point of migration history
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name=MODERATORS_GROUP)


def delete_moderators_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=MODERATORS_GROUP).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        # 0001 already depends on auth (the groups relation), so auth_group exists here
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_moderators_group, delete_moderators_group),
    ]
