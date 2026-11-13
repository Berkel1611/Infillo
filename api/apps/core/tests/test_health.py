import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_reports_database_ok() -> None:
    response = APIClient().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_rejects_other_methods() -> None:
    response = APIClient().post("/health")

    assert response.status_code == 405
