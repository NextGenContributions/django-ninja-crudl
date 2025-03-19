"""CRUDL API base class."""

import logging
from abc import ABC
from typing import TYPE_CHECKING, Literal

from django.db import transaction
from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from django.http import HttpRequest
from ninja_extra import http_patch, status

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

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import ManyRelatedManager

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)


def get_partial_update_endpoint(config: CrudlConfig[TDjangoModel_co]) -> type:
    """Create the partial update endpoint class for the CRUDL operations."""

    class PartialUpdateEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):
        @http_patch(
            path=config.update_path,
            operation_id=config.partial_update_operation_id,
            response={
                status.HTTP_200_OK: config.update_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            exclude_unset=True,
            by_alias=True,
        )
        @transaction.atomic
        @add_function_arguments(config.update_path)
        def patch(
            self,
            request: HttpRequest,
            payload: config.partial_update_schema,  # pyright: ignore[reportInvalidTypeForm, reportUnknownParameterType]
            **path_args: PathArgs,
        ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
            """Partial update an object."""
            request_details = RequestDetails[Model](
                action="patch",
                request=request,
                schema=config.partial_update_schema,  # pyright: ignore[reportPossiblyUnboundVariable]
                path_args=path_args,
                payload=payload,  # pyright: ignore[reportUnknownArgumentType]
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)  # noqa: WPS220
            obj: Model | None = (
                self.get_pre_filtered_queryset(config.model, path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_update(request_details))
                .first()
            )
            if obj is None:
                return self.get_404_error(request)  # noqa: WPS220
            request_details.object = obj
            if not self.has_object_permission(request_details):
                return self.get_404_error(request)  # noqa: WPS220

            for attr_name, attr_value in payload.items():
                try:
                    setattr(obj, attr_name, attr_value)
                except TypeError as e:
                    msg = "Direct assignment to the forward side of a many-to-many set is prohibited."
                    if msg in str(e):
                        m2m_manager: ManyRelatedManager[Model] = getattr(obj, attr_name)
                        m2m_manager.set(attr_value)
                    else:
                        raise
            obj.save()
            self.post_patch(request_details)
            return obj

    return PartialUpdateEndpoint
