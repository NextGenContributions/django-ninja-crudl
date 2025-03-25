"""Error handler mixin for the CRUDL views."""

from typing import Literal

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from django_ninja_crudl.errors.schemas import (
    Error403ForbiddenSchema,
    Error404NotFoundSchema,
    Error409ConflictSchema,
    Error503ServiceUnavailableSchema,
    ErrorSchema,
)
from django_ninja_crudl.errors.transform import get_exception_details


class ErrorHandlerMixin:
    """Error handler mixin for the CRUDL views."""

    def __init__(self) -> None:
        """Initialize the ErrorHandlerMixin class."""
        if type(self) is ErrorHandlerMixin:
            msg = "ErrorHandlerMixin is a mixin and shall not be instantiated directly."
            raise NotImplementedError(msg)

    def get_request_id(self, request: HttpRequest) -> str:
        """Return the request ID from the request headers.

        You may override this method to get the request ID from a different source.
        """
        return request.headers.get("X-Request-ID", "")

    def get_retry_after(self) -> int:
        """Return the number of seconds to wait before retrying the request.

        You may override this method to return a different value.
        """
        return 60

    def get_403_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,  # NOSONAR  # noqa: ARG002
        exception: Exception | None = None,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[403], Error403ForbiddenSchema]:
        """Return the 403 error message."""
        return 403, Error403ForbiddenSchema(request_id=self.get_request_id(request))

    def get_404_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,  # NOSONAR  # noqa: ARG002
        exception: Exception | None = None,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[404], ErrorSchema]:
        """Return the 404 error message."""
        return 404, Error404NotFoundSchema(request_id=self.get_request_id(request))

    def get_409_error(
        self,
        request: HttpRequest,
        response: HttpResponse | None = None,
        exception: Exception | None = None,
    ) -> tuple[Literal[409], ErrorSchema]:
        """Return the 409 error message."""
        if settings.DEBUG:
            # Log the exception in the console with full traceback.
            # full traceback
            import traceback

            traceback.print_exc()

        return 409, Error409ConflictSchema(
            request_id=self.get_request_id(request),
            details=get_exception_details(exception),
        )

    def get_503_error(
        self,
        request: HttpRequest,
        response: HttpResponse,
        exception: Exception,  # NOSONAR  # noqa: ARG002
    ) -> tuple[Literal[503], ErrorSchema]:
        """Return the 503 error message."""
        response["Retry-After"] = str(self.get_retry_after())

        return 503, Error503ServiceUnavailableSchema(
            request_id=self.get_request_id(request)
        )
