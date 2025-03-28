"""CRUDL API base class."""

from abc import ABC
from typing import Literal, Unpack

from django.db import transaction
from django.db.models import Model
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
    RequestDetails,
    RequestParams,
)
from django_ninja_crudl.utils import (
    replace_path_args_annotation,
    validating_manager,
)


def _create_schema_extra(config: CrudlConfig[Model]) -> JSON:
    """Create the OpenAPI links for the create operation.

    Ref: https://swagger.io/docs/specification/v3_0/links/
    """
    if config.create_response_schema is None:
        msg = "'create_response_schema' must be defined in Crudl config."
        raise ValueError(msg)

    create_response_name: str = config.create_response_schema.__name__
    get_one_operation_id: str = config.get_one_operation_id
    update_operation_id: str = config.update_operation_id
    partial_update_operation_id: str = config.partial_update_operation_id
    delete_operation_id: str = config.delete_operation_id
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


def get_create_endpoint(config: CrudlConfig[Model]) -> type:
    """Create the create endpoint class for the CRUDL operations."""

    class CreateEndpoint(CrudlBaseMethodsMixin[Model], ABC):
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
        @replace_path_args_annotation(config.create_path, config.model)
        def create_endpoint(
            self,
            request: HttpRequest,
            payload: config.create_schema,  # type: ignore[name-defined]
            **kwargs: Unpack[RequestParams],
        ) -> tuple[Literal[403, 404, 409], ErrorSchema] | tuple[Literal[201], Model]:
            """Create a new object."""
            request_details = RequestDetails[Model](
                action="create",
                request=request,
                schema=config.create_schema,
                path_args=self._get_path_args(kwargs),
                payload=payload,
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            self.pre_create(request_details)

            m2m_fields, obj_fields = self._get_fields_to_set(config.model, payload)

            # Create the object
            created_obj: Model | None = None

            def create() -> None:
                nonlocal created_obj
                with validating_manager(config.model):
                    # TODO(phuongfi91): should we use validating_manager later as well?
                    created_obj = config.model._default_manager.create(  # noqa: F841, SLF001
                        **dict(obj_fields),
                    )

            if create_err := self._try(create, request):
                return create_err
            if created_obj is None:
                return self.get_409_error(request)

            # Update many-to-many relationships on the created object
            if m2m_err := self._update_m2m_relationships(
                created_obj,
                m2m_fields,
                request,
                request_details,
            ):
                return m2m_err

            # Fully validate the created object as well as its related objects
            if clean_err := self._full_clean_obj(created_obj, request):
                return clean_err

            request_details.object = created_obj
            self.post_create(request_details)

            return 201, created_obj

    return CreateEndpoint
