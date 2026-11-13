import pytest
from rest_framework.test import APIClient

# Use the test URLconf above for every test in this module
pytestmark = pytest.mark.urls("apps.core.tests.urls")


def test_unknown_url_returns_not_found_code() -> None:
    response = APIClient().get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"code": "NOT_FOUND"}


def test_wrong_method_returns_method_not_allowed_code() -> None:
    response = APIClient().post("/health")

    assert response.status_code == 405
    assert response.json() == {"code": "METHOD_NOT_ALLOWED"}


def test_validation_error_lists_fields_with_codes() -> None:
    response = APIClient().post(
        "/test/validate", {"email": "not-an-email", "quantity": 0}, format="json"
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "fields": [
            {"field": "email", "type": "invalid"},
            {"field": "quantity", "type": "min_value"},
        ],
    }


def test_app_error_returns_code_status_and_params() -> None:
    response = APIClient().get("/test/app-error")

    assert response.status_code == 409
    assert response.json() == {"code": "OUT_OF_STOCK", "available": 2}


def test_unexpected_error_hides_exception_details() -> None:
    # By default the test client re-raises view exceptions; we want the real 500 response
    client = APIClient(raise_request_exception=False)

    response = client.get("/test/boom")

    assert response.status_code == 500
    assert response.json() == {"code": "INTERNAL_ERROR"}
    assert "secret detail" not in response.content.decode()
