"""Django Ninja CRUDL error handling module."""

from .mixin import ErrorHandlerMixin
from .openapi_extras import (
    not_authorized_openapi_extra,  # pyright: ignore[reportUnknownVariableType]
    throttle_openapi_extra,  # pyright: ignore[reportUnknownVariableType]
)
from .schemas import ErrorSchema
from .transform import (
    get_exception_details,
    transform_django_validation_error,
)

__all__ = [
    "ErrorHandlerMixin",
    "ErrorSchema",
    "get_exception_details",
    "not_authorized_openapi_extra",
    "throttle_openapi_extra",
    "transform_django_validation_error",
]
