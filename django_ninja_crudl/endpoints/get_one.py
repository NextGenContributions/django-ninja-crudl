"""CRUDL API base class."""

import logging
from abc import ABC
from typing import Literal

from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from django.http import HttpRequest
from ninja_extra import (
    http_get,
    status,
)

from django_ninja_crudl import CrudlConfig
from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error422UnprocessableEntitySchema,
    Error503ServiceUnavailableSchema,
    ErrorSchema,
)
from django_ninja_crudl.types import (
    PathArgs,
    RequestDetails,
    TDjangoModel,
    TDjangoModel_co,
)
from django_ninja_crudl.utils import add_function_arguments

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)


def get_get_one_endpoint(config: CrudlConfig[TDjangoModel_co]) -> type:
    """Create the get_one endpoint class for the CRUDL operations."""

    class GetOneEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):
        @http_get(
            path=config.get_one_path,
            response={
                status.HTTP_200_OK: config.get_one_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: ErrorSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            operation_id=config.get_one_operation_id,
            by_alias=True,
        )
        @add_function_arguments(config.get_one_path)
        def get_one(
            self,
            request: HttpRequest,
            **path_args: PathArgs,
        ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
            """Retrieve an object."""
            request_details = RequestDetails[Model](
                action="get_one",
                request=request,
                schema=config.get_one_schema,
                path_args=path_args,
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)  # noqa: WPS220

            obj = (
                self.get_pre_filtered_queryset(path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_get_one(request_details))
                .first()
            )
            if obj is None:
                return self.get_404_error(request)  # noqa: WPS220
            request_details.object = obj
            if not self.has_object_permission(request_details):
                return self.get_404_error(request)  # noqa: WPS220
            return obj

    return GetOneEndpoint
