"""API module for the project."""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest, HttpResponse
from ninja_extra import NinjaExtraAPI, status
from src.databases.ninja import DatabaseCrudl

from .errors import ErrorSchema

api = NinjaExtraAPI()

api.register_controllers(DatabaseCrudl)
# api.register_controllers(EndpointCrudl)


@api.exception_handler(ObjectDoesNotExist)
def key_error_handler(request: HttpRequest, exc: ObjectDoesNotExist) -> HttpResponse:
    """Handle KeyError exceptions."""
    error = ErrorSchema(
        code=exc.__class__.__name__,
        message=str(exc),
        request_id=request.headers.get("X-Request-ID", ""),
    )
    return api.create_response(
        request,
        error,
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@api.exception_handler(ValidationError)
def validation_error_handler(
    request: HttpRequest,
    exc: ValidationError,
) -> HttpResponse:
    """Handle ValidationError exceptions."""
    error = ErrorSchema(
        code=exc.__class__.__name__,
        message=str(exc),
        request_id=request.headers.get("X-Request-ID", ""),
    )
    return api.create_response(
        request,
        error,
        status=status.HTTP_409_CONFLICT,
    )


"""
django.core.exceptions.ValidationError: {'__all__': ['Database with this Name and Organization already exists.']}
--> 409 Conflict
"""
