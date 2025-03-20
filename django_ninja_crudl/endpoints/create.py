"""CRUDL API base class."""

from abc import ABC
from enum import Enum, IntEnum
from typing import Any, Literal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from django.http import HttpRequest
from ninja_extra import http_post, status

from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.config import CrudlConfig
from django_ninja_crudl.errors.openapi_extras import (
    not_authorized_openapi_extra,
    throttle_openapi_extra,
)
from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error404NotFoundSchema,
    Error409ConflictSchema,
    Error422UnprocessableEntitySchema,
    Error503ServiceUnavailableSchema,
    ErrorSchema,
)
from django_ninja_crudl.types import (
    JSON,
    PathArgs,
    RequestDetails,
    TDjangoModel,
    TDjangoModel_co,
)
from django_ninja_crudl.utils import add_function_arguments, validating_manager


def _create_schema_extra(
    config: CrudlConfig[TDjangoModel_co],
) -> JSON:
    """Create the OpenAPI links for the create operation.

    Ref: https://swagger.io/docs/specification/v3_0/links/
    """
    get_one_operation_id: str = config.get_one_operation_id
    update_operation_id: str = config.update_operation_id
    partial_update_operation_id: str = config.partial_update_operation_id
    delete_operation_id: str = config.delete_operation_id
    create_response_name: str = config.create_response_name
    resource_name: str = config.model.__name__.lower()

    res_body_id = "$response.body#/id"
    return {
        "responses": {
            201: {
                "description": "Created",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{create_response_name}",
                        },
                    },
                },
                "links": {
                    "UpdateById": {
                        "operationId": update_operation_id,
                        "parameters": {"id": res_body_id},
                        "description": f"Update {resource_name} by id",
                    },
                    "DeleteById": {
                        "operationId": delete_operation_id,
                        "parameters": {"id": res_body_id},
                        "description": f"Delete {resource_name} by id",
                    },
                    "GetById": {
                        "operationId": get_one_operation_id,
                        "parameters": {"id": res_body_id},
                        "description": f"Get {resource_name} by id",
                    },
                    "PatchById": {
                        "operationId": partial_update_operation_id,
                        "parameters": {"id": res_body_id},
                        "description": f"Patch {resource_name} by id",
                    },
                },
            },
            **not_authorized_openapi_extra,
            **throttle_openapi_extra,
        },
    }

def get_create_endpoint(config: CrudlConfig[TDjangoModel_co]) -> type:
    """Create the create endpoint class for the CRUDL operations."""
    create_schema = config.create_schema

    class CreateEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):
        """Create endpoint for CRUDL operations."""

        @http_post(
            path=config.create_path,
            operation_id=config.create_operation_id,
            response={
                status.HTTP_201_CREATED: config.create_response_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_409_CONFLICT: Error409ConflictSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            openapi_extra=_create_schema_extra(config),
        )
        @transaction.atomic
        @add_function_arguments(config.create_path)
        def create_endpoint(
            self,
            request: HttpRequest,
            payload: create_schema,
            **path_args: PathArgs,
        ) -> tuple[Literal[403, 404, 409], ErrorSchema] | tuple[Literal[201], Model]:
            """Create a new object."""
            request_details = RequestDetails[TDjangoModel_co](
                action="create",
                request=request,
                schema=config.create_schema,
                path_args=path_args,
                payload=payload,
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            self.pre_create(request_details)

            obj_fields_to_set: list[tuple[str, Any]] = []  # pyright: ignore[reportExplicitAny]
            m2m_fields_to_set: list[tuple[str, Any]] = []  # pyright: ignore[reportExplicitAny]

            for field, field_value in payload.model_dump().items():
                if isinstance(field_value, Enum | IntEnum):
                    field_value = field_value.value  # noqa: PLW2901, WPS220
                if isinstance(
                    config.model._meta.get_field(field),  # noqa: SLF001, WPS437
                    ManyToManyField | ManyToManyRel | ManyToOneRel | OneToOneRel,
                ):
                    m2m_fields_to_set.append((field, field_value))
                else:
                    # Handle foreign key fields:
                    if isinstance(  # noqa: WPS220, WPS337
                        config.model._meta.get_field(field),  # noqa: SLF001, WPS437
                        ForeignKey,
                    ) and not field.endswith("_id"):
                        field_name = f"{field}_id"
                    else:  # Non-relational fields
                        field_name = field

                    obj_fields_to_set.append((field_name, field_value))
            try:
                with validating_manager(config.model):
                    created_obj: Model = config.model._default_manager.create(  # noqa: SLF001
                        **dict(obj_fields_to_set),
                    )
            # if integrity error, return 409
            except IntegrityError as integrity_error:
                transaction.set_rollback(True)
                return self.get_409_error(request, exception=integrity_error)

            for (
                m2m_field,
                m2m_field_value,
            ) in m2m_fields_to_set:  # pyright: ignore[reportAny]
                related_model_class = self._get_related_model(config.model, m2m_field)  # pyright: ignore[reportPrivateUsage]

                if isinstance(m2m_field_value, list):
                    for m2m_field_value_item in m2m_field_value:
                        related_obj = related_model_class._default_manager.get(
                            id=m2m_field_value_item,
                        )
                        request_details_related = request_details  # noqa: WPS220
                        request_details_related.related_model_class = (
                            related_model_class
                        )
                        request_details_related.related_object = related_obj
                        if not self.has_related_object_permission(
                            request_details_related,
                        ):
                            transaction.set_rollback(True)
                            return self.get_404_error(request)
                else:
                    related_obj = related_model_class._default_manager.get(
                        id=m2m_field_value,
                    )

                    if not self.has_related_object_permission(request_details):
                        transaction.set_rollback(True)
                        return self.get_404_error(request)

                try:
                    getattr(created_obj, m2m_field).set(m2m_field_value)
                except IntegrityError:
                    transaction.set_rollback(True)  # noqa: WPS220
                    return self.get_409_error(request)

            # Perform full_clean() on the created object
            # and raise an exception if it fails
            try:
                created_obj.full_clean()
            except ValidationError as validation_error:
                # revert the transaction
                transaction.set_rollback(True)
                return self.get_409_error(request, exception=validation_error)

            request_details.object = created_obj
            self.post_create(request_details)
            return 201, created_obj

    return CreateEndpoint
