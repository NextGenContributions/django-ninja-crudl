"""Exception handlers."""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest, HttpResponse
from ninja_extra import status


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


def authorization_error_handler(
    request: HttpRequest,
    exc: AuthorizationError,
) -> HttpResponse:
    """Handle AuthorizationError exceptions."""
    error = ErrorSchema(
        code=exc.__class__.__name__,
        message=str(exc),
        request_id=request.headers.get("X-Request-ID", ""),
    )
    return api.create_response(
        request,
        error,
        status=status.HTTP_401_UNAUTHORIZED,
    )
