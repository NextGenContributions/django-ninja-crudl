"""Error handler mixin for the CRUDL views."""

from typing import Literal

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error404NotFoundSchema,
    Error409ConflictSchema,
    Error503ServiceUnavailableSchema,
    ErrorSchema,
)
from django_ninja_crudl.errors.transform import get_exception_details
from django_ninja_crudl.utils import get_request_id


class ErrorHandlerMixin:
    """Error handler mixin for the CRUDL views."""

    def __init__(self) -> None:
        """Initialize the ErrorHandlerMixin class."""
        if type(self) is ErrorHandlerMixin:
            msg = "ErrorHandlerMixin is a mixin and shall not be instantiated directly."
            raise NotImplementedError(msg)

    def get_retry_after(self) -> int:
        """Return the number of seconds to wait before retrying the request.

        You may override this method to return a different value.
        """
        return 60

    def get_401_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,  # NOSONAR  # noqa: ARG002
        exception: Exception | None = None,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[401], ErrorSchema]:
        """Return the 401 error message."""
        return 401, Error401UnauthorizedSchema(request_id=get_request_id(request))

    def get_403_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,  # NOSONAR  # noqa: ARG002
        exception: Exception | None = None,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[403], Error403ForbiddenSchema]:
        """Return the 403 error message."""
        return 403, Error403ForbiddenSchema(request_id=get_request_id(request))

    def get_404_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,  # NOSONAR  # noqa: ARG002
        exception: Exception | None = None,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[404], ErrorSchema]:
        """Return the 404 error message."""
        return 404, Error404NotFoundSchema(request_id=get_request_id(request))

    def get_409_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,  # NOSONAR  # noqa: ARG002
        exception: Exception | None = None,
    ) -> tuple[Literal[409], ErrorSchema]:
        """Return the 409 error message."""
        if settings.DEBUG:
            # Log the exception in the console with full traceback.
            # full traceback
            import traceback

            traceback.print_exc()

        return 409, Error409ConflictSchema(
            request_id=get_request_id(request),
            detail=get_exception_details(exception),
        )

    def get_503_error(
        self,
        request: HttpRequest,
        response: HttpResponse,
        exception: Exception,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[503], ErrorSchema]:
        """Return the 503 error message."""
        response["Retry-After"] = str(self.get_retry_after())

        return 503, Error503ServiceUnavailableSchema(request_id=get_request_id(request))
