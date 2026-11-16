import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.accounts.models import MODERATORS_GROUP

User = get_user_model()


def make_users(count: int) -> None:
    for index in range(count):
        User.objects.create_user(
            email=f"u{index}@test.pl",
            username=f"user{index}",
            password="BardzoTajne1",
            first_name="U",
            last_name=str(index),
        )


def emails(response) -> set[str]:
    return {item["email"] for item in response.json()["results"]}


# --- GET /users ---


def test_admin_gets_paginated_list_with_roles(
    login, regular_user, moderator, administrator
) -> None:
    response = login(administrator).get("/users")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 3
    roles = {item["email"]: item["role"] for item in body["results"]}
    assert roles == {"user@test.pl": "user", "mod@test.pl": "moderator", "admin@test.pl": "admin"}
    assert all("password" not in item for item in body["results"])


@pytest.mark.parametrize(
    ("role", "expected"),
    [("user", {"user@test.pl"}), ("moderator", {"mod@test.pl"}), ("admin", {"admin@test.pl"})],
)
def test_list_filters_by_role(
    login, regular_user, moderator, administrator, role, expected
) -> None:
    response = login(administrator).get("/users", {"role": role})

    assert response.status_code == 200
    assert emails(response) == expected


def test_superuser_in_moderators_group_is_listed_only_as_admin(
    login, regular_user, moderator, administrator
) -> None:
    administrator.groups.add(Group.objects.get(name=MODERATORS_GROUP))
    client = login(administrator)

    assert emails(client.get("/users", {"role": "moderator"})) == {"mod@test.pl"}
    assert emails(client.get("/users", {"role": "admin"})) == {"admin@test.pl"}


def test_list_rejects_unknown_role(login, administrator) -> None:
    response = login(administrator).get("/users", {"role": "boss"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert {"field": "role", "type": "invalid_choice"} in response.json()["fields"]


def test_list_searches_by_email_ignoring_case(
    login, regular_user, moderator, administrator
) -> None:
    client = login(administrator)

    assert emails(client.get("/users", {"search": "MOD"})) == {"mod@test.pl"}
    assert emails(client.get("/users", {"search": "test.pl"})) == {
        "user@test.pl",
        "mod@test.pl",
        "admin@test.pl",
    }
    # "%" is escaped, so it is not a wildcard
    assert client.get("/users", {"search": "%"}).json()["count"] == 0


def test_list_is_paginated(login, administrator) -> None:
    make_users(25)  # plus the administrator = 26 accounts
    client = login(administrator)

    first = client.get("/users").json()
    assert first["count"] == 26
    assert len(first["results"]) == 20
    assert first["next"] is not None

    last = client.get("/users", {"page": 3, "page_size": 10}).json()
    assert len(last["results"]) == 6
    assert last["next"] is None


def test_list_does_not_query_groups_per_user(
    login, administrator, django_assert_max_num_queries
) -> None:
    make_users(15)
    client = login(administrator)

    # authentication + count + page + groups prefetch; an N+1 would add about 15 more
    with django_assert_max_num_queries(6):
        response = client.get("/users")

    assert response.status_code == 200


def test_list_is_for_admins_only(login, regular_user, moderator) -> None:
    anonymous = APIClient().get("/users")
    assert anonymous.status_code == 401
    assert anonymous.json() == {"code": "NOT_AUTHENTICATED"}

    for user in (regular_user, moderator):
        response = login(user).get("/users")
        assert response.status_code == 403
        assert response.json() == {"code": "FORBIDDEN"}


# --- PATCH /users/{id} ---


def test_admin_grants_and_revokes_moderator_role(login, regular_user, administrator) -> None:
    client = login(administrator)

    granted = client.patch(f"/users/{regular_user.id}", {"role": "moderator"}, format="json")

    assert granted.status_code == 200
    assert granted.json()["role"] == "moderator"  # fresh, not a stale prefetch cache
    assert regular_user.groups.filter(name=MODERATORS_GROUP).exists()

    revoked = client.patch(f"/users/{regular_user.id}", {"role": "user"}, format="json")

    assert revoked.status_code == 200
    assert revoked.json()["role"] == "user"
    assert not regular_user.groups.exists()


def test_block_takes_effect_immediately_and_can_be_undone(
    login, regular_user, administrator
) -> None:
    admin_client = login(administrator)
    user_client = login(regular_user)
    assert user_client.get("/auth/me").status_code == 200

    blocked = admin_client.patch(f"/users/{regular_user.id}", {"is_active": False}, format="json")

    assert blocked.status_code == 200
    assert blocked.json()["is_active"] is False
    assert user_client.get("/auth/me").status_code == 401  # the old cookie stopped working

    admin_client.patch(f"/users/{regular_user.id}", {"is_active": True}, format="json")

    assert user_client.get("/auth/me").status_code == 200


def test_role_and_block_can_be_changed_together(login, regular_user, administrator) -> None:
    payload = {"role": "moderator", "is_active": False}

    response = login(administrator).patch(f"/users/{regular_user.id}", payload, format="json")

    assert response.status_code == 200
    assert response.json()["role"] == "moderator"
    assert response.json()["is_active"] is False


def test_empty_patch_changes_nothing(login, regular_user, administrator) -> None:
    response = login(administrator).patch(f"/users/{regular_user.id}", {}, format="json")

    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert response.json()["is_active"] is True


def test_admin_cannot_modify_self(login, administrator) -> None:
    client = login(administrator)

    for payload in ({"role": "user"}, {"is_active": False}):
        response = client.patch(f"/users/{administrator.id}", payload, format="json")

        assert response.status_code == 400
        assert response.json() == {"code": "CANNOT_MODIFY_SELF"}
    administrator.refresh_from_db()
    assert administrator.is_active


def test_admin_cannot_modify_another_admin(login, administrator) -> None:
    other = User.objects.create_superuser(
        email="admin2@test.pl",
        username="admin2",
        password="BardzoTajne1",
        first_name="Ewa",
        last_name="Admin",
    )

    response = login(administrator).patch(f"/users/{other.id}", {"is_active": False}, format="json")

    assert response.status_code == 400
    assert response.json() == {"code": "CANNOT_MODIFY_ADMIN"}
    other.refresh_from_db()
    assert other.is_active


@pytest.mark.parametrize("role", ["admin", "boss"])
def test_role_other_than_user_or_moderator_is_rejected(
    login, regular_user, administrator, role
) -> None:
    response = login(administrator).patch(
        f"/users/{regular_user.id}", {"role": role}, format="json"
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert {"field": "role", "type": "invalid_choice"} in response.json()["fields"]
    regular_user.refresh_from_db()
    assert regular_user.role == "user"


@pytest.mark.parametrize("user_id", ["999999", "abc"])
def test_unknown_user_returns_404_with_code(login, administrator, user_id: str) -> None:
    response = login(administrator).patch(f"/users/{user_id}", {"role": "moderator"}, format="json")

    assert response.status_code == 404
    assert response.json() == {"code": "USER_NOT_FOUND"}


def test_patch_is_for_admins_only(login, regular_user, moderator) -> None:
    path = f"/users/{regular_user.id}"
    assert APIClient().patch(path, {"is_active": False}, format="json").status_code == 401

    for user in (regular_user, moderator):
        assert login(user).patch(path, {"is_active": False}, format="json").status_code == 403
    regular_user.refresh_from_db()
    assert regular_user.is_active


def test_other_methods_on_a_user_are_not_allowed(login, regular_user, administrator) -> None:
    client = login(administrator)
    path = f"/users/{regular_user.id}"

    assert client.get(path).status_code == 405
    assert client.put(path, {"role": "moderator"}, format="json").status_code == 405
    assert client.delete(path).status_code == 405
