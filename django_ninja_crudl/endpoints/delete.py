"""CRUDL API base class."""

from abc import ABC
from typing import Literal

from django.db import transaction
from django.db.models import Model
from django.http import HttpRequest
from ninja_extra import http_delete, status

from django_ninja_crudl import CrudlConfig
from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error404NotFoundSchema,
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


def get_delete_endpoint(config: CrudlConfig[TDjangoModel_co]) -> type:
    """Create the delete endpoint class for the CRUDL operations."""

    class DeleteEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):
        @http_delete(
            path=config.delete_path,
            operation_id=config.delete_operation_id,
            response={
                status.HTTP_204_NO_CONTENT: None,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
        )
        @transaction.atomic
        @add_function_arguments(config.delete_path)
        def delete(
            self,
            request: HttpRequest,
            **path_args: PathArgs,
        ) -> tuple[Literal[403, 404], ErrorSchema] | tuple[Literal[204], None]:
            """Delete the object by id."""
            request_details = RequestDetails[Model](
                action="delete",
                request=request,
                path_args=path_args,
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)

            obj = (
                self.get_pre_filtered_queryset(config.model, path_args)
                .filter(self.get_filter_for_delete(request_details))
                .first()
            )
            if obj is None:
                return self.get_404_error(request)
            request_details.object = obj
            if not self.has_object_permission(request_details):
                return self.get_404_error(request)
            self.pre_delete(request_details)
            _ = obj.delete()
            self.post_delete(request_details)
            return 204, None

    return DeleteEndpoint
