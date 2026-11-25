from datetime import timedelta

import pytest
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.catalog.models import Category

pytestmark = pytest.mark.django_db


def make(name: str, parent: Category | None = None, position: int = 0) -> Category:
    return Category.objects.create(name=name, parent=parent, position=position)


def code(response) -> str:
    return response.json()["code"]


# --- GET /categories ---


def test_list_is_public_and_nested():
    home = make("Dom", position=1)
    make("Figurki", position=0)
    make("Organizery", home)

    response = APIClient().get("/categories")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)  # a plain tree, not a paginated envelope
    assert [node["name"] for node in body] == ["Figurki", "Dom"]
    assert set(body[1]) == {"id", "name", "children"}
    assert body[0]["children"] == []
    assert body[1]["children"] == [
        {"id": Category.objects.get(name="Organizery").id, "name": "Organizery", "children": []}
    ]


def test_list_with_expired_cookie_still_200(regular_user):
    # Review Focus 2: a stale cookie must not turn a public catalog into a 401
    expired = AccessToken.for_user(regular_user)
    expired.set_exp(lifetime=-timedelta(minutes=1))
    client = APIClient()
    client.cookies[settings.AUTH_COOKIE_NAME] = str(expired)

    assert client.get("/categories").status_code == 200


# --- permissions ---


def test_write_requires_admin(login, regular_user, moderator):
    category = make("Dom")
    requests = [
        ("post", "/categories", {"name": "Nowa"}),
        ("patch", f"/categories/{category.id}", {"name": "Zmieniona"}),
        ("delete", f"/categories/{category.id}", None),
    ]
    for method, url, payload in requests:
        guest = getattr(APIClient(), method)(url, payload, format="json")
        assert guest.status_code == 401, (method, url)
        for user in (regular_user, moderator):
            response = getattr(login(user), method)(url, payload, format="json")
            assert response.status_code == 403, (method, url, user.username)

    category.refresh_from_db()
    assert category.name == "Dom"
    assert Category.objects.count() == 1


# --- POST /categories ---


def test_create_201_returns_the_category(login, administrator):
    home = make("Dom")

    response = login(administrator).post(
        "/categories", {"name": "  Organizery ", "parent_id": home.id}, format="json"
    )

    assert response.status_code == 201
    created = Category.objects.get(name="Organizery")
    assert response.json() == {"id": created.id, "name": "Organizery", "parent_id": home.id}


def test_create_root_without_parent_id(login, administrator):
    response = login(administrator).post("/categories", {"name": "Dom"}, format="json")

    assert response.status_code == 201
    assert response.json()["parent_id"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 101},
        {"name": "Dom", "parent_id": 999_999},
        {"name": "Dom", "parent_id": "abc"},
    ],
)
def test_create_validation_errors_400(login, administrator, payload):
    response = login(administrator).post("/categories", payload, format="json")

    assert response.status_code == 400
    assert code(response) == "VALIDATION_ERROR"
    assert Category.objects.count() == 0


def test_name_taken_409(login, administrator):
    make("Dom")

    response = login(administrator).post("/categories", {"name": "dom"}, format="json")

    assert response.status_code == 409
    assert code(response) == "CATEGORY_NAME_TAKEN"


def test_create_too_deep_400(login, administrator):
    level1 = make("L1")
    level2 = make("L2", level1)
    level3 = make("L3", level2)

    response = login(administrator).post(
        "/categories", {"name": "L4", "parent_id": level3.id}, format="json"
    )

    assert response.status_code == 400
    assert code(response) == "CATEGORY_TOO_DEEP"


# --- PATCH /categories/{id} ---


def test_patch_rename_and_move(login, administrator):
    home = make("Dom")
    gifts = make("Prezenty")
    category = make("Organizery", home)

    response = login(administrator).patch(
        f"/categories/{category.id}", {"name": "Uchwyty", "parent_id": gifts.id}, format="json"
    )

    assert response.status_code == 200
    assert response.json() == {"id": category.id, "name": "Uchwyty", "parent_id": gifts.id}


def test_patch_partial_and_move_to_root(login, administrator):
    home = make("Dom")
    category = make("Organizery", home)
    client = login(administrator)

    only_name = client.patch(f"/categories/{category.id}", {"name": "Pudelka"}, format="json")
    assert only_name.json()["parent_id"] == home.id  # parent untouched

    to_root = client.patch(f"/categories/{category.id}", {"parent_id": None}, format="json")
    assert to_root.status_code == 200
    assert to_root.json() == {"id": category.id, "name": "Pudelka", "parent_id": None}


def test_patch_cycle_and_too_deep_400(login, administrator):
    root = make("L1")
    middle = make("L2", root)
    leaf = make("L3", middle)
    other = make("Inne")
    make("Inne dziecko", other)
    client = login(administrator)

    cycle = client.patch(f"/categories/{root.id}", {"parent_id": leaf.id}, format="json")
    assert (cycle.status_code, code(cycle)) == (400, "CATEGORY_CYCLE")

    deep = client.patch(f"/categories/{other.id}", {"parent_id": middle.id}, format="json")
    assert (deep.status_code, code(deep)) == (400, "CATEGORY_TOO_DEEP")


def test_patch_name_taken_409(login, administrator):
    make("Dom")
    category = make("Prezenty")

    response = login(administrator).patch(
        f"/categories/{category.id}", {"name": "dom"}, format="json"
    )

    assert (response.status_code, code(response)) == (409, "CATEGORY_NAME_TAKEN")


def test_patch_validation_400(login, administrator):
    category = make("Dom")

    for payload in ({"name": "  "}, {"name": "x" * 101}, {"parent_id": 999_999}):
        response = login(administrator).patch(f"/categories/{category.id}", payload, format="json")
        assert (response.status_code, code(response)) == (400, "VALIDATION_ERROR"), payload


# --- DELETE /categories/{id} ---


def test_delete_empty_204(login, administrator):
    category = make("Dom")

    response = login(administrator).delete(f"/categories/{category.id}")

    assert response.status_code == 204
    assert not Category.objects.filter(pk=category.pk).exists()


def test_delete_not_empty_409(login, administrator):
    parent = make("Dom")
    make("Organizery", parent)

    response = login(administrator).delete(f"/categories/{parent.id}")

    assert (response.status_code, code(response)) == (409, "CATEGORY_NOT_EMPTY")
    assert Category.objects.count() == 2


# --- unknown id ---


def test_unknown_id_404_category_not_found(login, administrator):
    client = login(administrator)

    patch = client.patch("/categories/999999", {"name": "X"}, format="json")
    delete = client.delete("/categories/999999")

    for response in (patch, delete):
        assert (response.status_code, code(response)) == (404, "CATEGORY_NOT_FOUND")
