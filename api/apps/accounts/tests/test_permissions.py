import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.urls("apps.accounts.tests.urls")


@pytest.mark.parametrize("path", ["/test/admin-only", "/test/staff-only"])
def test_anonymous_gets_401(path: str) -> None:
    response = APIClient().get(path)

    assert response.status_code == 401
    assert response.json() == {"code": "NOT_AUTHENTICATED"}


@pytest.mark.parametrize(
    ("who", "expected_status"),
    [("regular_user", 403), ("moderator", 403), ("administrator", 200)],
)
def test_is_admin(who: str, expected_status: int, request, login) -> None:
    client = login(request.getfixturevalue(who))

    response = client.get("/test/admin-only")

    assert response.status_code == expected_status
    if expected_status == 403:
        assert response.json() == {"code": "FORBIDDEN"}


@pytest.mark.parametrize(
    ("who", "expected_status"),
    [("regular_user", 403), ("moderator", 200), ("administrator", 200)],
)
def test_is_moderator_or_admin(who: str, expected_status: int, request, login) -> None:
    client = login(request.getfixturevalue(who))

    response = client.get("/test/staff-only")

    assert response.status_code == expected_status
