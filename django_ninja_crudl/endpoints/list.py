"""CRUDL API base class."""

import logging
from abc import ABC

from django.db import models
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneField,
    OneToOneRel,
)
from django.http import HttpRequest, HttpResponse
from ninja_extra import http_get, status

from django_ninja_crudl import CrudlConfig
from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error422UnprocessableEntitySchema,
    Error503ServiceUnavailableSchema,
    ErrorSchema,
)
from django_ninja_crudl.model_utils import get_pydantic_fields
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


def get_get_many_endpoint(config: CrudlConfig[TDjangoModel_co]) -> type:
    """Create the get_many endpoint class for the CRUDL operations."""

    class GetManyEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):
        """GetMany endpoint for CRUDL operations."""

        @http_get(
            path=config.list_path,
            response={
                200: list[config.list_schema],  # pyright: ignore[reportPossiblyUnboundVariable]
                401: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                422: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            operation_id=config.list_operation_id,
            # openapi_extra=config.openapi_extra,
        )
        @add_function_arguments(config.list_path)
        def get_many(  # noqa: WPS210
            self,
            request: HttpRequest,
            response: HttpResponse,
            **path_args: PathArgs,
        ) -> tuple[int, ErrorSchema] | models.Manager[Model]:
            """List all objects."""
            request_details = RequestDetails[Model](
                action="list",
                request=request,
                path_args=path_args,
                model_class=config.model,
            )

            if not self.has_permission(request_details):
                return self.get_403_error(request)

            qs = (
                self.get_pre_filtered_queryset(config.model, path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_list(request_details))
            )

            # Return the total count of objects in the response headers
            response["x-total-count"] = qs.count()

            # Extract the related models from the ListSchema fields
            related_models: list[str] = []
            many_to_many_models: list[str] = []
            related_fields: list[str] = []
            property_fields: list[str] = []

            for field_name in config.list_schema.model_fields:
                attr = getattr(config.model, field_name, None)  # noqa: WPS220

                # Skip @property methods here
                if attr and isinstance(attr, property):
                    property_fields.append(field_name)  # noqa: WPS220
                    # TODO: Implement a way to avoid N+1 queries when using @property methods
                    logger.debug(  # noqa: WPS220
                        "Detected use of @property method %s of the model %s in"
                        " list_fields definition which"
                        " may cause N+1 queries and cause performance degradation.",
                        field_name,
                        config.model,
                    )
                    return qs  # noqa: WPS220

                django_field = config.model._meta.get_field(field_name)  # noqa: SLF001
                if isinstance(
                    django_field,
                    OneToOneField | ForeignKey,
                ):
                    related_models.append(field_name)  # noqa: WPS220
                    related_fields.extend(  # noqa: WPS220
                        get_pydantic_fields(
                            config.list_schema,
                            field_name,
                        ),
                    )

                elif isinstance(  # noqa: WPS220
                    django_field,
                    ManyToManyField,
                ):
                    many_to_many_models.append(field_name)  # noqa: WPS220
                    related_fields.extend(  # noqa: WPS220
                        get_pydantic_fields(
                            config.list_schema,
                            field_name,
                        ),
                    )
                    # related_models.append(f"{field_name}__id")

            non_related_fields: list[str] = [
                field_name
                for field_name in config.list_schema.model_fields.keys()
                if field_name
                not in related_models + many_to_many_models + property_fields
            ]

            all_fields: list[str] = non_related_fields + related_fields

            qs = qs.select_related(*related_models).prefetch_related(
                *many_to_many_models,
            )  # To avoid N+1 queries
            qs = qs.values(*all_fields)
            return qs

    return GetManyEndpoint
