"""CRUDL API base class."""

from abc import ABC
from typing import TYPE_CHECKING, Literal, Unpack, cast

from django.db import transaction
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
    TDjangoModel,
)
from django_ninja_crudl.utils import (
    replace_path_args_annotation,
    validating_manager,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


def _create_schema_extra(config: CrudlConfig[TDjangoModel]) -> JSON:
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
            status.HTTP_201_CREATED: {
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
            **not_authorized_openapi_extra,  # type: ignore[dict-item]
            **throttle_openapi_extra,  # type: ignore[dict-item]
        }
    }


def get_create_endpoint(config: CrudlConfig[TDjangoModel]) -> type | None:
    """Create the create endpoint class for the CRUDL operations."""
    if not config.create_schema or not config.create_response_schema:
        return None

    create_schema: type[BaseModel] = config.create_schema
    create_response_schema: type[BaseModel] = config.create_response_schema

    class CreateEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):  # pyright: ignore [reportGeneralTypeIssues]
        """Create endpoint for CRUDL operations."""

        @http_post(
            path=config.create_path,
            operation_id=config.create_operation_id,
            response={
                status.HTTP_201_CREATED: create_response_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_409_CONFLICT: Error409ConflictSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            openapi_extra=_create_schema_extra(config),  # type: ignore[arg-type]
        )
        @transaction.atomic
        @replace_path_args_annotation(config.create_path, config.model)
        def create_endpoint(
            self,
            request: HttpRequest,
            payload: create_schema,  # type: ignore[valid-type]
            **kwargs: Unpack[RequestParams],
        ) -> (
            tuple[Literal[403, 404, 409], ErrorSchema]
            | tuple[Literal[201], TDjangoModel]
        ):
            """Create a new object."""
            request_details = RequestDetails[TDjangoModel](
                action="create",
                request=request,
                schema=create_schema,
                path_args=self._get_path_args(kwargs),
                payload=payload,
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            self.pre_create(request_details)

            simple_fields, relational_fields = self._get_fields_to_set(
                config.model, payload
            )

            # Create the object
            created_obj: TDjangoModel | None = None

            def create() -> None:
                nonlocal created_obj
                with validating_manager(config.model):
                    # TODO(phuongfi91): should we use validating_manager later as well?
                    created_obj = config.model._default_manager.create(  # noqa: F841, SLF001
                        **dict(simple_fields),
                    )

            if create_err := self._try(create, request):
                return create_err

            # The object is guaranteed to be created at this point
            created_obj = cast(TDjangoModel, created_obj)  # pyright: ignore[reportInvalidCast]

            # Update complex relations on the created object
            if rel_err := self._update_complex_relations(
                created_obj,
                relational_fields,
                request,
                request_details,
            ):
                return rel_err

            # Fully validate the created object as well as its related objects
            if clean_err := self._full_clean_obj(created_obj, request):
                return clean_err

            request_details.object = created_obj
            self.post_create(request_details)

            return 201, created_obj

    return CreateEndpoint
