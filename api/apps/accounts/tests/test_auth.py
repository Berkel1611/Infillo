from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

PASSWORD = "BardzoTajne1"
COOKIE = settings.AUTH_COOKIE_NAME

pytestmark = pytest.mark.django_db

REGISTER_PAYLOAD = {
    "email": "new@test.pl",
    "username": "newbie",
    "password": PASSWORD,
    "first_name": "Jan",
    "last_name": "Kowalski",
}


def register_payload(**overrides: str) -> dict[str, str]:
    return {**REGISTER_PAYLOAD, **overrides}


def post_json(client: APIClient, path: str, payload: dict):
    return client.post(path, payload, format="json")


# --- registration ---


def test_register_creates_user_and_logs_in() -> None:
    client = APIClient()

    response = post_json(client, "/auth/register", REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@test.pl"
    assert body["username"] == "newbie"
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert "password" not in body
    cookie = response.cookies[COOKIE]
    assert cookie.value
    assert cookie["httponly"] is True
    user = User.objects.get(email="new@test.pl")
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)
    # The cookie from registration already authenticates the client
    assert client.get("/auth/me").json()["email"] == "new@test.pl"


def test_register_ignores_role_fields_in_request() -> None:
    payload = register_payload(role="admin", is_superuser=True, is_staff=True)

    response = post_json(APIClient(), "/auth/register", payload)

    assert response.status_code == 201
    user = User.objects.get(email="new@test.pl")
    assert user.role == "user"
    assert not user.is_superuser
    assert not user.is_staff


def test_register_normalizes_email_and_rejects_duplicate_in_other_case() -> None:
    post_json(APIClient(), "/auth/register", register_payload(email="  New@Test.PL "))
    assert User.objects.get().email == "new@test.pl"

    response = post_json(
        APIClient(), "/auth/register", register_payload(email="NEW@test.pl", username="other")
    )

    assert response.status_code == 409
    assert response.json() == {"code": "EMAIL_TAKEN"}
    assert User.objects.count() == 1


def test_register_rejects_taken_username_in_other_case() -> None:
    post_json(APIClient(), "/auth/register", REGISTER_PAYLOAD)

    response = post_json(
        APIClient(), "/auth/register", register_payload(email="other@test.pl", username="NEWBIE")
    )

    assert response.status_code == 409
    assert response.json() == {"code": "USERNAME_TAKEN"}


@pytest.mark.parametrize(
    ("password", "code"),
    [
        ("abc1", "password_too_short"),
        ("12345678", "password_entirely_numeric"),
        ("password", "password_too_common"),
        ("newbie12", "password_too_similar"),  # similar to the username "newbie"
    ],
)
def test_register_rejects_weak_passwords_with_validator_code(password: str, code: str) -> None:
    response = post_json(APIClient(), "/auth/register", register_payload(password=password))

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert {"field": "password", "type": code} in body["fields"]
    assert not User.objects.exists()


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("email", "not-an-email", "invalid"),
        ("username", "ab", "min_length"),
        ("username", "has space", "invalid_username"),
        ("username", "bad@name", "invalid_username"),
        ("first_name", "", "blank"),
    ],
)
def test_register_rejects_invalid_fields(field: str, value: str, error_type: str) -> None:
    response = post_json(APIClient(), "/auth/register", register_payload(**{field: value}))

    assert response.status_code == 400
    assert {"field": field, "type": error_type} in response.json()["fields"]


def test_register_requires_all_fields() -> None:
    response = post_json(APIClient(), "/auth/register", {})

    assert response.status_code == 400
    required = {(item["field"], item["type"]) for item in response.json()["fields"]}
    assert required == {(name, "required") for name in REGISTER_PAYLOAD}


# --- login ---


@pytest.mark.parametrize("identifier", ["user@test.pl", "  User@Test.PL ", "regular", "REGULAR"])
def test_login_with_email_or_username(regular_user, identifier: str) -> None:
    client = APIClient()

    response = post_json(client, "/auth/login", {"login": identifier, "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["email"] == "user@test.pl"
    assert response.cookies[COOKIE].value
    assert client.get("/auth/me").status_code == 200


def test_login_with_wrong_password_returns_401(regular_user) -> None:
    response = post_json(APIClient(), "/auth/login", {"login": "regular", "password": "Nope12345"})

    assert response.status_code == 401
    assert response.json() == {"code": "INVALID_CREDENTIALS"}
    assert COOKIE not in response.cookies


def test_login_with_unknown_account_returns_401() -> None:
    response = post_json(
        APIClient(), "/auth/login", {"login": "nobody@test.pl", "password": PASSWORD}
    )

    assert response.status_code == 401
    assert response.json() == {"code": "INVALID_CREDENTIALS"}


def test_login_to_blocked_account_returns_401(regular_user) -> None:
    regular_user.is_active = False
    regular_user.save()

    response = post_json(APIClient(), "/auth/login", {"login": "regular", "password": PASSWORD})

    assert response.status_code == 401
    assert response.json() == {"code": "INVALID_CREDENTIALS"}


def test_login_to_account_without_password_returns_401(regular_user) -> None:
    regular_user.set_unusable_password()
    regular_user.save()

    response = post_json(APIClient(), "/auth/login", {"login": "regular", "password": PASSWORD})

    assert response.status_code == 401
    assert response.json() == {"code": "INVALID_CREDENTIALS"}


def test_login_requires_both_fields() -> None:
    response = post_json(APIClient(), "/auth/login", {})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "attack", ["' OR '1'='1", "x' OR '1'='1' --@test.pl", "'; DROP TABLE accounts_user; --"]
)
def test_sql_injection_in_login_is_harmless(regular_user, attack: str) -> None:
    payloads = [
        {"login": attack, "password": PASSWORD},
        {"login": "user@test.pl", "password": attack},
        {"login": attack, "password": attack},
    ]

    for payload in payloads:
        response = post_json(APIClient(), "/auth/login", payload)

        assert response.status_code in (400, 401)
        assert COOKIE not in response.cookies

    assert User.objects.filter(pk=regular_user.pk).exists()  # the table is still there


def test_login_works_with_an_expired_cookie_present(regular_user) -> None:
    token = AccessToken.for_user(regular_user)
    token.set_exp(lifetime=-timedelta(minutes=1))
    client = APIClient()
    client.cookies[COOKIE] = str(token)

    response = post_json(client, "/auth/login", {"login": "regular", "password": PASSWORD})

    assert response.status_code == 200


def test_django_admin_login_accepts_email(administrator) -> None:
    response = Client().post(
        "/admin/login/", {"username": "admin@test.pl", "password": PASSWORD, "next": "/admin/"}
    )

    assert response.status_code == 302  # success redirects; a failure would render the form (200)


# --- logout and current user ---


def test_logout_clears_cookie_and_ends_the_session(regular_user) -> None:
    client = APIClient()
    post_json(client, "/auth/login", {"login": "regular", "password": PASSWORD})
    assert client.get("/auth/me").status_code == 200

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert response.cookies[COOKIE]["max-age"] == 0
    assert client.get("/auth/me").status_code == 401


def test_logout_without_login_or_with_garbage_cookie_returns_204() -> None:
    client = APIClient()
    assert client.post("/auth/logout").status_code == 204

    client.cookies[COOKIE] = "garbage"
    assert client.post("/auth/logout").status_code == 204


def test_me_without_cookie_returns_401() -> None:
    response = APIClient().get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"code": "NOT_AUTHENTICATED"}


def test_me_returns_current_user_without_password(login, moderator) -> None:
    response = login(moderator).get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "mod@test.pl"
    assert body["role"] == "moderator"
    assert "password" not in body
    assert set(body) == {
        "id",
        "email",
        "username",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "date_joined",
    }
