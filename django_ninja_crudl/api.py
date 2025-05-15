"""Django Ninja CRUDL API."""

import logging
import traceback
from collections.abc import Callable, Sequence
from typing import Any, override

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from ninja import errors as ninja_exceptions
from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.openapi.docs import DocsBase, Swagger
from ninja.openapi.schema import OpenAPISchema
from ninja.params.models import TModel
from ninja.parser import Parser
from ninja.renderers import BaseRenderer
from ninja.throttling import BaseThrottle
from ninja.types import DictStrAny, TCallable
from ninja_extra import NinjaExtraAPI, status
from ninja_extra import exceptions as ninja_extra_exceptions

from django_ninja_crudl.errors.schemas import (
    Error404NotFoundSchema,
    Error422UnprocessableEntitySchema,
    Error500InternalServerErrorSchema,
    ErrorSchema,
)
from django_ninja_crudl.utils import get_request_id

logger = logging.getLogger("django")


class NinjaCrudlOpenAPISchema(OpenAPISchema):
    """OpenAPI schema for the CRUDL API."""

    @override
    def _extract_parameters(self, model: TModel) -> list[DictStrAny]:  # pyright: ignore [reportInvalidTypeVarUse]
        """Extract parameters from the model."""
        result = super()._extract_parameters(model)
        # Remove "examples" from the parameters as they are just copies of "examples"
        # in the pydantic schemas, which is a list of values and not a dict. This is
        # problematic because Parameters' "examples" is supposed to be a dict.
        # Assigning a list to it would cause issue with API docs and schemathesis tests.
        for param in result:
            _ = param.pop("examples", None)  # pyright: ignore [reportAny]
        return result


class NinjaCrudlAPI(NinjaExtraAPI):
    """Ninja Extra API with CRUDL support."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        title: str = "NinjaExtraAPI",
        version: str = "1.0.0",
        description: str = "",
        openapi_url: str | None = "/openapi.json",
        docs: DocsBase | None = None,
        docs_url: str | None = "/docs",
        docs_decorator: Callable[[TCallable], TCallable] | None = None,
        servers: list[DictStrAny] | None = None,
        urls_namespace: str | None = None,
        csrf: bool = False,
        auth: Sequence[Callable] | Callable | NOT_SET_TYPE | None = NOT_SET,  # type: ignore[type-arg]
        throttle: BaseThrottle | list[BaseThrottle] | NOT_SET_TYPE = NOT_SET,
        renderer: BaseRenderer | None = None,
        parser: Parser | None = None,
        openapi_extra: dict[str, Any] | None = None,  # pyright: ignore [reportExplicitAny]
        app_name: str = "ninja",
        **kwargs: Any,  # noqa: ANN401  # pyright: ignore [reportExplicitAny, reportAny]
    ) -> None:
        """Initialize Ninja CRUDL API.

        Args:
            title: A title for the api.
            version: The API version.
            description: A description for the api.
            openapi_url: The relative URL to serve the openAPI spec.
            docs: API documentation class.
            docs_url: The relative URL to serve the API docs.
            docs_decorator: A decorator for the API docs view.
            servers: List of target hosts used in openAPI spec.
            urls_namespace: The Django URL namespace for the API. If not provided,
                the namespace will be ``"api-" + self.version``.
            csrf: Require a CSRF token for unsafe request types.
                See <a href="../csrf">CSRF</a> docs.
            auth: Authentication class or classes.
            throttle: Throttling class or list of throttling classes.
            renderer: Default response renderer.
            parser: Default request parser.
            openapi_extra: Additional attributes for the openAPI spec.
            app_name: The name of the Django app.
            kwargs: Additional keyword arguments.
        """
        if not docs:
            docs = Swagger()

        super().__init__(  # pyright: ignore [reportUnknownMemberType]
            title=title,
            version=version,
            description=description,
            openapi_url=openapi_url,
            docs=docs,
            docs_url=docs_url,
            docs_decorator=docs_decorator,
            servers=servers,
            urls_namespace=urls_namespace,
            csrf=csrf,
            auth=auth,
            throttle=throttle,
            renderer=renderer,
            parser=parser,
            openapi_extra=openapi_extra,
            app_name=app_name,
            **kwargs,
        )

    @override
    def set_default_exception_handlers(self) -> None:
        """Override the default exception handlers set by django-ninja."""
        self.exception_handler(Exception)(self._default_exception)
        self.exception_handler(Http404)(self._default_404)
        self.exception_handler(ninja_exceptions.HttpError)(self._default_http_error)
        self.exception_handler(ninja_exceptions.ValidationError)(
            self._default_validation_error
        )

    @override
    def api_exception_handler(
        self, request: HttpRequest, exc: ninja_extra_exceptions.APIException
    ) -> HttpResponse:
        """Override and handle generic django-ninja-extra's API exceptions."""
        headers: dict = {}  # type: ignore[type-arg]
        if isinstance(exc, ninja_extra_exceptions.Throttled):
            headers["Retry-After"] = f"{float(exc.wait or 0.0):d}"  # type: ignore[redundant-expr]

        data = ErrorSchema(
            request_id=get_request_id(request),
            detail=exc.detail,  # pyright: ignore [reportArgumentType]
            code=exc.__class__.__name__,
        )
        response = self.create_response(request, data, status=exc.status_code)
        for k, v in headers.items():  # pyright: ignore [reportUnknownVariableType]
            response.setdefault(k, v)  # pyright: ignore [reportUnknownArgumentType]

        return response

    def _default_404(self, request: HttpRequest, exc: Exception) -> HttpResponse:
        """Handle Django's 404 errors."""
        msg = "Not Found"
        if settings.DEBUG:  # pyright: ignore [reportAny]
            msg += f": {exc}"
        data = Error404NotFoundSchema(
            request_id=get_request_id(request),
            detail=msg,
        )
        return self.create_response(request, data, status=status.HTTP_404_NOT_FOUND)

    def _default_http_error(
        self, request: HttpRequest, exc: ninja_exceptions.HttpError
    ) -> HttpResponse:
        """Handle generic django-ninja HTTP errors."""
        data = ErrorSchema(
            request_id=get_request_id(request),
            detail=str(exc),
            code=exc.__class__.__name__,
        )
        return self.create_response(request, data, status=exc.status_code)

    def _default_validation_error(
        self, request: HttpRequest, exc: ninja_exceptions.ValidationError
    ) -> HttpResponse:
        """Handle django-ninja validation errors."""
        data = Error422UnprocessableEntitySchema(
            request_id=get_request_id(request),
            detail=exc.errors,
        )
        return self.create_response(
            request, data, status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    def _default_exception(self, request: HttpRequest, exc: Exception) -> HttpResponse:
        """Handle generic server errors."""
        logger.exception(exc)
        tb = traceback.format_exc() if settings.DEBUG else None  # pyright: ignore [reportAny]
        data = Error500InternalServerErrorSchema(
            request_id=get_request_id(request),
            detail=tb,
        )
        return self.create_response(
            request, data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @override
    def get_openapi_schema(
        self,
        *,
        path_prefix: str | None = None,
        path_params: DictStrAny | None = None,
    ) -> OpenAPISchema:
        """Get the OpenAPI schema for the API."""
        if path_prefix is None:
            path_prefix = self.get_root_path(path_params or {})
        return NinjaCrudlOpenAPISchema(self, path_prefix)
