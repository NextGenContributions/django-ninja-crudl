"""CRUDL API base class."""

import logging
from abc import ABC
from typing import Literal

from django.db import transaction
from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from django.http import HttpRequest
from ninja_extra import http_put, status

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


def get_update_endpoint(config: CrudlConfig[TDjangoModel_co]) -> type:
    """Create the update endpoint class for the CRUDL operations."""
    update_schema = config.update_schema

    class UpdateEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):
        """Base class for the CRUDL API."""

        @http_put(
            path=config.update_path,
            operation_id=config.update_operation_id,
            response={
                status.HTTP_200_OK: config.update_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: ErrorSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            by_alias=True,
        )
        @transaction.atomic
        @add_function_arguments(config.update_path)
        def update(
            self,
            request: HttpRequest,
            payload: update_schema,
            **path_args: PathArgs,
        ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
            """Update an object."""
            request_details = RequestDetails[TDjangoModel_co](
                action="put",
                request=request,
                schema=config.update_schema,
                path_args=path_args,
                payload=payload,
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            obj = (
                self.get_pre_filtered_queryset(path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_update(request_details))
                .first()
            )

            if obj is None:
                return self.get_404_error(request)
            request_details.object = obj
            if not self.has_object_permission(request_details):
                return self.get_404_error(request)
            self.pre_update(request_details)

            for attr_name, attr_value in payload.model_dump().items():
                setattr(obj, attr_name, attr_value)
            obj.save()
            self.post_update(request_details)
            return obj

    return UpdateEndpoint
