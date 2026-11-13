"""Error contract: every API error has the shape {"code": "...", ...params}."""

from collections.abc import Iterator
from typing import Any

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

STATUS_CODES = {
    401: "NOT_AUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    415: "UNSUPPORTED_MEDIA_TYPE",
    429: "TOO_MANY_REQUESTS",
}


class AppError(exceptions.APIException):
    """Expected business error returned as {"code": ..., **params}."""

    def __init__(self, code: str, status_code: int = 400, **params: Any) -> None:
        super().__init__(detail=code, code=code)
        self.status_code = status_code
        self.error_code = code
        self.params = params


def _field_errors(detail: Any, field: str = "") -> Iterator[dict[str, str]]:
    """Flatten DRF validation details into [{"field": "email", "type": "invalid"}, ...]."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            yield from _field_errors(value, f"{field}.{key}" if field else str(key))
    elif isinstance(detail, list):
        for index, item in enumerate(detail):
            if isinstance(item, dict | list):  # nested serializer inside a list
                yield from _field_errors(item, f"{field}.{index}" if field else str(index))
            else:
                yield from _field_errors(item, field)
    else:
        # ErrorDetail is a str with an extra .code ("required", "invalid", "max_length"...)
        yield {"field": field or "non_field_errors", "type": getattr(detail, "code", "invalid")}


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # unexpected error -> Django's handler500

    if isinstance(exc, AppError):
        response.data = {"code": exc.error_code, **exc.params}
    elif isinstance(exc, exceptions.ValidationError):
        response.data = {"code": "VALIDATION_ERROR", "fields": list(_field_errors(exc.detail))}
    else:
        response.data = {"code": STATUS_CODES.get(response.status_code, "HTTP_ERROR")}
    return response
