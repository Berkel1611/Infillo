from datetime import timedelta

import jwt
import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.http import HttpResponse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.authentication import clear_auth_cookie, set_auth_cookie
from apps.accounts.models import MODERATORS_GROUP

pytestmark = pytest.mark.urls("apps.accounts.tests.urls")

COOKIE = settings.AUTH_COOKIE_NAME


def test_auth_cookie_is_httponly_lax_and_lives_8_hours(regular_user) -> None:
    response = HttpResponse()

    set_auth_cookie(response, regular_user)

    cookie = response.cookies[COOKIE]
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/"
    assert cookie["max-age"] == 8 * 3600
    assert str(AccessToken(cookie.value)["user_id"]) == str(regular_user.id)


def test_clear_auth_cookie_expires_it() -> None:
    response = HttpResponse()

    clear_auth_cookie(response)

    assert response.cookies[COOKIE].value == ""
    assert response.cookies[COOKIE]["max-age"] == 0


def test_valid_cookie_authenticates_user(login, regular_user) -> None:
    response = login(regular_user).get("/test/whoami")

    assert response.status_code == 200
    assert response.json() == {"email": "user@test.pl", "role": "user"}


def test_no_cookie_returns_401() -> None:
    response = APIClient().get("/test/whoami")

    assert response.status_code == 401
    assert response.json() == {"code": "NOT_AUTHENTICATED"}


def test_garbage_and_forged_tokens_return_401(regular_user) -> None:
    forged = jwt.encode({"user_id": regular_user.id}, "x" * 48, algorithm="HS256")

    for token in ("not-a-jwt", forged):
        client = APIClient()
        client.cookies[COOKIE] = token
        response = client.get("/test/whoami")

        assert response.status_code == 401
        assert response.json() == {"code": "NOT_AUTHENTICATED"}


def test_expired_token_returns_401(regular_user) -> None:
    token = AccessToken.for_user(regular_user)
    token.set_exp(lifetime=-timedelta(minutes=1))
    client = APIClient()
    client.cookies[COOKIE] = str(token)

    response = client.get("/test/whoami")

    assert response.status_code == 401


def test_blocked_user_is_rejected_immediately(login, regular_user) -> None:
    client = login(regular_user)
    regular_user.is_active = False
    regular_user.save()

    assert client.get("/test/whoami").status_code == 401


def test_deleted_user_is_rejected(login, regular_user) -> None:
    client = login(regular_user)
    regular_user.delete()

    assert client.get("/test/whoami").status_code == 401


def test_role_change_applies_to_existing_token(login, regular_user) -> None:
    client = login(regular_user)
    assert client.get("/test/whoami").json()["role"] == "user"

    regular_user.groups.add(Group.objects.get(name=MODERATORS_GROUP))

    assert client.get("/test/whoami").json()["role"] == "moderator"
