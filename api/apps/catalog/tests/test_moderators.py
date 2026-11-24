import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from rest_framework.test import APIClient

from apps.accounts.models import MODERATORS_GROUP
from apps.catalog.models import Category, CategoryModerator
from apps.catalog.services import (
    category_moderators,
    managed_category_ids,
    set_category_moderators,
)
from apps.core.exceptions import AppError

pytestmark = pytest.mark.django_db
User = get_user_model()


def make(name: str, parent: Category | None = None) -> Category:
    return Category.objects.create(name=name, parent=parent)


def make_moderator(username: str):
    user = User.objects.create_user(
        email=f"{username}@test.pl",
        username=username,
        password="BardzoTajne1",
        first_name="M",
        last_name=username,
    )
    user.groups.add(Group.objects.get(name=MODERATORS_GROUP))
    return user


def assign(category: Category, *users) -> None:
    for user in users:
        CategoryModerator.objects.create(category=category, moderator=user)


def usernames(users) -> list[str]:
    return [user.username for user in users]


# --- services: assignment ---


def test_set_replaces_assignments():
    category = make("Dom")
    first, second, third = (make_moderator(name) for name in ("anna", "bartek", "celina"))
    assign(category, first, second)

    result = set_category_moderators(category, [second.id, third.id])

    assert usernames(result) == ["bartek", "celina"]
    assert usernames(category_moderators(category)) == ["bartek", "celina"]
    assert CategoryModerator.objects.filter(category=category).count() == 2


def test_set_empty_list_clears_and_duplicates_are_harmless():
    category = make("Dom")
    moderator = make_moderator("anna")

    assert usernames(set_category_moderators(category, [moderator.id, moderator.id])) == ["anna"]
    assert set_category_moderators(category, []) == []
    assert CategoryModerator.objects.count() == 0


def test_non_moderator_rejected_400(regular_user, administrator):
    category = make("Dom")
    moderator = make_moderator("anna")
    assign(category, moderator)

    for bad_id in (regular_user.id, administrator.id, 999_999):
        with pytest.raises(AppError) as exc:
            set_category_moderators(category, [moderator.id, bad_id])
        assert exc.value.error_code == "USER_NOT_MODERATOR"
        assert exc.value.status_code == 400

    # a rejected request changes nothing
    assert usernames(category_moderators(category)) == ["anna"]


def test_list_hides_users_who_lost_role():
    # Review Focus 3: the assignment row stays, but it grants and shows nothing
    category = make("Dom")
    stays, loses = make_moderator("anna"), make_moderator("bartek")
    assign(category, stays, loses)
    loses.groups.clear()

    assert usernames(category_moderators(category)) == ["anna"]
    assert CategoryModerator.objects.filter(category=category).count() == 2


# --- services: management scope ---


def test_managed_ids_admin_all(administrator):
    root = make("Dom")
    child = make("Organizery", root)
    other = make("Figurki")

    assert managed_category_ids(administrator) == {root.id, child.id, other.id}


def test_managed_ids_moderator_includes_descendants(moderator):
    root = make("Dom")
    child = make("Organizery", root)
    grandchild = make("Pudelka", child)
    make("Figurki")
    assign(child, moderator)

    assert managed_category_ids(moderator) == {child.id, grandchild.id}
    assign(root, moderator)
    assert managed_category_ids(moderator) == {root.id, child.id, grandchild.id}


def test_managed_ids_user_and_anonymous_empty(regular_user):
    category = make("Dom")
    assign(category, regular_user)  # a stale or forged row must not grant anything

    assert managed_category_ids(regular_user) == set()
    assert managed_category_ids(AnonymousUser()) == set()


def test_managed_ids_ignores_user_who_lost_role(moderator):
    category = make("Dom")
    assign(category, moderator)
    moderator.groups.clear()

    assert managed_category_ids(moderator) == set()


# --- API ---


def test_moderators_endpoints_admin_only(login, regular_user, moderator):
    category = make("Dom")
    for method, payload in (("get", None), ("put", {"moderator_ids": []})):
        url = f"/categories/{category.id}/moderators"
        assert getattr(APIClient(), method)(url, payload, format="json").status_code == 401
        for user in (regular_user, moderator):
            response = getattr(login(user), method)(url, payload, format="json")
            assert response.status_code == 403


def test_put_and_get_moderators(login, administrator):
    category = make("Dom")
    anna, bartek = make_moderator("anna"), make_moderator("bartek")
    client = login(administrator)

    put = client.put(
        f"/categories/{category.id}/moderators",
        {"moderator_ids": [bartek.id, anna.id]},
        format="json",
    )
    assert put.status_code == 200
    expected = [{"id": anna.id, "username": "anna"}, {"id": bartek.id, "username": "bartek"}]
    assert put.json() == expected
    assert client.get(f"/categories/{category.id}/moderators").json() == expected


def test_put_moderators_errors(login, administrator, regular_user):
    category = make("Dom")
    client = login(administrator)
    url = f"/categories/{category.id}/moderators"

    not_moderator = client.put(url, {"moderator_ids": [regular_user.id]}, format="json")
    assert (not_moderator.status_code, not_moderator.json()["code"]) == (400, "USER_NOT_MODERATOR")

    for payload in ({}, {"moderator_ids": "1"}, {"moderator_ids": ["a"]}):
        invalid = client.put(url, payload, format="json")
        assert (invalid.status_code, invalid.json()["code"]) == (400, "VALIDATION_ERROR")

    missing = client.get("/categories/999999/moderators")
    assert (missing.status_code, missing.json()["code"]) == (404, "CATEGORY_NOT_FOUND")


def test_managed_endpoint_roles(login, regular_user):
    assert APIClient().get("/categories/managed").status_code == 401
    assert login(regular_user).get("/categories/managed").status_code == 403


def test_managed_returns_flat_scope(login, administrator, moderator):
    root = make("Dom")
    child = make("Organizery", root)
    make("Figurki")
    assign(root, moderator)

    as_moderator = login(moderator).get("/categories/managed")
    assert as_moderator.status_code == 200
    assert as_moderator.json() == [
        {"id": root.id, "name": "Dom", "parent_id": None},
        {"id": child.id, "name": "Organizery", "parent_id": root.id},
    ]

    as_admin = login(administrator).get("/categories/managed")
    assert [item["name"] for item in as_admin.json()] == ["Dom", "Figurki", "Organizery"]
