import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import MODERATORS_GROUP, ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER

User = get_user_model()

PASSWORD = "BardzoTajne1"


def make_user(email: str = "jan@test.pl", username: str = "jan", password: str | None = PASSWORD):
    return User.objects.create_user(
        email=email, username=username, password=password, first_name="Jan", last_name="Kowalski"
    )


@pytest.mark.django_db
def test_create_user_normalizes_email_and_hashes_password() -> None:
    user = make_user(email="  Jan.Kowalski@Test.PL ")

    assert user.email == "jan.kowalski@test.pl"
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_user_without_password_cannot_log_in_with_one() -> None:
    user = make_user(password=None)

    assert not user.has_usable_password()
    assert not user.check_password("")


@pytest.mark.django_db
def test_create_superuser_sets_admin_flags() -> None:
    admin = User.objects.create_superuser(
        email="admin@test.pl",
        username="admin",
        password=PASSWORD,
        first_name="Ada",
        last_name="Admin",
    )

    assert admin.is_staff
    assert admin.is_superuser


def test_create_user_requires_email() -> None:
    with pytest.raises(ValueError):
        User.objects.create_user(email="", username="jan", password=PASSWORD)


def test_create_user_requires_username() -> None:
    with pytest.raises(ValueError):
        User.objects.create_user(email="jan@test.pl", username="", password=PASSWORD)


@pytest.mark.django_db
def test_email_is_unique_regardless_of_case() -> None:
    make_user(email="jan@test.pl", username="jan")

    with pytest.raises(IntegrityError):
        make_user(email="JAN@test.pl", username="jan2")


@pytest.mark.django_db
def test_username_is_unique_regardless_of_case() -> None:
    make_user(email="jan@test.pl", username="SmokowyDrukarz")

    with pytest.raises(IntegrityError):
        make_user(email="inny@test.pl", username="smokowydrukarz")


@pytest.mark.parametrize("username", ["jan@test.pl", "ab", "jan kowalski"])
def test_invalid_usernames_are_rejected(username: str) -> None:
    user = User(email="jan@test.pl", username=username, first_name="Jan", last_name="Kowalski")
    user.set_password("BardzoTajne1")

    with pytest.raises(ValidationError) as error:
        user.full_clean(validate_unique=False, validate_constraints=False)

    assert "username" in error.value.message_dict


@pytest.mark.django_db
def test_moderators_group_is_created_by_migration() -> None:
    # No fixture and no manual create: the data migration 0002 made it
    assert Group.objects.filter(name=MODERATORS_GROUP).exists()


@pytest.mark.django_db
def test_role_user_moderator_and_admin() -> None:
    regular = make_user(email="user@test.pl", username="regular")
    moderator = make_user(email="mod@test.pl", username="moderator")
    moderator.groups.add(Group.objects.get(name=MODERATORS_GROUP))
    admin = User.objects.create_superuser(
        email="admin@test.pl",
        username="admin",
        password=PASSWORD,
        first_name="Ada",
        last_name="Admin",
    )

    assert regular.role == ROLE_USER
    assert moderator.role == ROLE_MODERATOR
    assert admin.role == ROLE_ADMIN


@pytest.mark.django_db
def test_superuser_in_moderators_group_is_still_admin() -> None:
    admin = User.objects.create_superuser(
        email="admin@test.pl",
        username="admin",
        password=PASSWORD,
        first_name="Ada",
        last_name="Admin",
    )
    admin.groups.add(Group.objects.get(name=MODERATORS_GROUP))

    assert admin.role == ROLE_ADMIN


@pytest.mark.django_db
def test_role_uses_prefetched_groups_without_extra_queries(django_assert_num_queries) -> None:
    make_user(email="one@test.pl", username="one")
    moderator = make_user(email="two@test.pl", username="two")
    moderator.groups.add(Group.objects.get(name=MODERATORS_GROUP))

    users = list(User.objects.prefetch_related("groups"))

    # Roles of all users are computed from the prefetched cache: zero queries
    with django_assert_num_queries(0):
        roles = {user.username: user.role for user in users}

    assert roles == {"one": ROLE_USER, "two": ROLE_MODERATOR}
