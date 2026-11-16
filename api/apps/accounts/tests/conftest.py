import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponse
from rest_framework.test import APIClient

from apps.accounts.authentication import set_auth_cookie
from apps.accounts.models import MODERATORS_GROUP

User = get_user_model()
PASSWORD = "BardzoTajne1"


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        email="user@test.pl",
        username="regular",
        password=PASSWORD,
        first_name="Jan",
        last_name="Kowalski",
    )


@pytest.fixture
def moderator(db):
    user = User.objects.create_user(
        email="mod@test.pl",
        username="moderator",
        password=PASSWORD,
        first_name="Maria",
        last_name="Nowak",
    )
    user.groups.add(Group.objects.get(name=MODERATORS_GROUP))
    return user


@pytest.fixture
def administrator(db):
    return User.objects.create_superuser(
        email="admin@test.pl",
        username="admin",
        password=PASSWORD,
        first_name="Ada",
        last_name="Admin",
    )


@pytest.fixture
def login():
    """Returns a function: login(user) -> APIClient with the auth cookie, like after /auth/login."""

    def _login(user) -> APIClient:
        response = HttpResponse()
        set_auth_cookie(response, user)
        client = APIClient()
        client.cookies[settings.AUTH_COOKIE_NAME] = response.cookies[
            settings.AUTH_COOKIE_NAME
        ].value
        return client

    return _login
