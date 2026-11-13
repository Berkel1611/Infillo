import pytest
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from apps.core.pagination import StandardPagination


def paginate(items: list[int], **query: int):
    """Runs the paginator on a plain list (no database needed)."""
    request = Request(APIRequestFactory().get("/items", query))
    paginator = StandardPagination()
    return paginator.paginate_queryset(items, request), paginator


def test_default_page_size_is_20_and_response_has_count() -> None:
    page, paginator = paginate(list(range(50)))

    assert len(page) == 20
    body = paginator.get_paginated_response(page).data
    assert body["count"] == 50
    assert set(body) == {"count", "next", "previous", "results"}


def test_client_can_choose_page_size() -> None:
    page, _ = paginate(list(range(50)), page_size=5)

    assert len(page) == 5


def test_page_size_is_capped_at_100() -> None:
    page, _ = paginate(list(range(300)), page_size=1000)

    assert len(page) == 100


@pytest.mark.urls("apps.core.tests.urls")
def test_only_json_bodies_are_accepted() -> None:
    response = APIClient().post(
        "/test/validate", {"email": "a@test.pl", "quantity": 1}, format="multipart"
    )

    assert response.status_code == 415
    assert response.json() == {"code": "UNSUPPORTED_MEDIA_TYPE"}
