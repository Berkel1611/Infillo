import pytest
from rest_framework.test import APIClient

from apps.accounts.models import ShippingAddress

ADDRESS = {
    "street": "Ul. Lipowa 1/2",
    "postal_code": "15-001",
    "city": "Białystok",
    "phone": "+48 600 100 200",
}


# --- profile: PATCH /auth/me ---


def test_patch_changes_only_given_fields(login, regular_user) -> None:
    response = login(regular_user).patch("/auth/me", {"first_name": "Janusz"}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Janusz"
    assert body["last_name"] == "Kowalski"
    assert body["username"] == "regular"
    regular_user.refresh_from_db()
    assert regular_user.first_name == "Janusz"


def test_patch_changes_username_first_and_last_name(login, regular_user) -> None:
    payload = {"username": "new.name", "first_name": "Anna", "last_name": "Nowak"}

    response = login(regular_user).patch("/auth/me", payload, format="json")

    assert response.status_code == 200
    assert response.json()["username"] == "new.name"
    regular_user.refresh_from_db()
    assert (regular_user.username, regular_user.first_name, regular_user.last_name) == (
        "new.name",
        "Anna",
        "Nowak",
    )


def test_patch_allows_changing_the_case_of_own_username(login, regular_user) -> None:
    response = login(regular_user).patch("/auth/me", {"username": "REGULAR"}, format="json")

    assert response.status_code == 200
    assert response.json()["username"] == "REGULAR"


def test_patch_rejects_username_taken_by_someone_else(login, regular_user, moderator) -> None:
    response = login(regular_user).patch("/auth/me", {"username": "MODERATOR"}, format="json")

    assert response.status_code == 409
    assert response.json() == {"code": "USERNAME_TAKEN"}
    regular_user.refresh_from_db()
    assert regular_user.username == "regular"


@pytest.mark.parametrize(
    ("payload", "field", "error_type"),
    [
        ({"username": "ab"}, "username", "min_length"),
        ({"username": "bad@name"}, "username", "invalid_username"),
        ({"first_name": ""}, "first_name", "blank"),
        ({"last_name": "x" * 81}, "last_name", "max_length"),
    ],
)
def test_patch_validates_fields(login, regular_user, payload, field, error_type) -> None:
    response = login(regular_user).patch("/auth/me", payload, format="json")

    assert response.status_code == 400
    assert {"field": field, "type": error_type} in response.json()["fields"]


def test_patch_cannot_change_email_role_or_flags(login, regular_user) -> None:
    payload = {"email": "hacker@test.pl", "role": "admin", "is_superuser": True, "is_staff": True}

    response = login(regular_user).patch("/auth/me", payload, format="json")

    assert response.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.email == "user@test.pl"
    assert regular_user.role == "user"
    assert not regular_user.is_superuser
    assert not regular_user.is_staff


def test_patch_with_empty_body_changes_nothing(login, regular_user) -> None:
    response = login(regular_user).patch("/auth/me", {}, format="json")

    assert response.status_code == 200
    assert response.json()["username"] == "regular"


def test_patch_requires_login_and_put_is_not_allowed(login, regular_user) -> None:
    assert APIClient().patch("/auth/me", {}, format="json").status_code == 401
    assert login(regular_user).put("/auth/me", {}, format="json").status_code == 405


# --- address: GET / PUT /auth/me/address ---


def test_address_is_null_until_saved(login, regular_user) -> None:
    response = login(regular_user).get("/auth/me/address")

    assert response.status_code == 200
    assert response.json() is None


def test_put_creates_then_overwrites_the_single_address(login, regular_user) -> None:
    client = login(regular_user)

    created = client.put("/auth/me/address", ADDRESS, format="json")
    assert created.status_code == 200
    body = created.json()
    assert {key: body[key] for key in ADDRESS} == ADDRESS
    assert "updated_at" in body

    changed = client.put("/auth/me/address", {**ADDRESS, "city": "Warszawa"}, format="json")
    assert changed.status_code == 200
    assert ShippingAddress.objects.filter(user=regular_user).count() == 1
    assert client.get("/auth/me/address").json()["city"] == "Warszawa"


def test_phone_is_optional(login, regular_user) -> None:
    payload = {key: value for key, value in ADDRESS.items() if key != "phone"}

    response = login(regular_user).put("/auth/me/address", payload, format="json")

    assert response.status_code == 200
    assert response.json()["phone"] == ""


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("postal_code", "15001", "invalid_postal_code"),
        ("postal_code", "15-0011", "max_length"),
        ("postal_code", "ab-cde", "invalid_postal_code"),
        ("phone", "abc", "invalid_phone"),
        ("street", "", "blank"),
        ("city", "x" * 101, "max_length"),
    ],
)
def test_put_validates_fields(login, regular_user, field, value, error_type) -> None:
    response = login(regular_user).put("/auth/me/address", {**ADDRESS, field: value}, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert {"field": field, "type": error_type} in response.json()["fields"]
    assert not ShippingAddress.objects.exists()


def test_put_requires_street_postal_code_and_city(login, regular_user) -> None:
    response = login(regular_user).put("/auth/me/address", {}, format="json")

    assert response.status_code == 400
    required = {(item["field"], item["type"]) for item in response.json()["fields"]}
    assert required == {("street", "required"), ("postal_code", "required"), ("city", "required")}


def test_users_see_only_their_own_address(login, regular_user, moderator) -> None:
    login(regular_user).put("/auth/me/address", ADDRESS, format="json")

    assert login(moderator).get("/auth/me/address").json() is None
    assert login(regular_user).get("/auth/me/address").json()["street"] == ADDRESS["street"]


@pytest.mark.parametrize("method", ["get", "put"])
def test_address_requires_login(method: str) -> None:
    response = getattr(APIClient(), method)("/auth/me/address", ADDRESS, format="json")

    assert response.status_code == 401
    assert response.json() == {"code": "NOT_AUTHENTICATED"}


@pytest.mark.django_db
def test_address_is_deleted_together_with_the_user(regular_user) -> None:
    ShippingAddress.objects.create(
        user=regular_user, street="Lipowa 1", postal_code="15-001", city="Białystok"
    )

    regular_user.delete()

    assert not ShippingAddress.objects.exists()
