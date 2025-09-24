"""CRUDL API base class."""

import weakref
from abc import ABC
from typing import TYPE_CHECKING, Literal, Unpack

from django.db import transaction
from django.db.models.signals import ModelSignal, post_save, pre_save
from django.dispatch.dispatcher import _make_id  # type: ignore[attr-defined]
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
    RegisteredReceiver,
    RequestDetails,
    RequestParams,
    TDjangoModel,
)
from django_ninja_crudl.utils import (
    replace_path_args_annotation,
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
            url_name=config.create_operation_id,
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
            tuple[Literal[401, 403, 404, 409], ErrorSchema]
            | tuple[Literal[201], TDjangoModel]
        ):
            """Create a new object."""
            request_details = RequestDetails[TDjangoModel](
                action="create",
                request=request,
                schema=create_schema,
                path_args=self._get_path_args(kwargs),
                payload=payload,  # pyright: ignore [reportUnknownArgumentType]
                model_class=config.model,
            )
            if not self.is_authenticated(request_details):
                return self.get_401_error(request)
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            self.pre_create(request_details)

            simple_fields, property_fields, simple_relations, complex_relations = (
                self._get_fields_to_set(
                    config.model,
                    payload,  # pyright: ignore [reportUnknownArgumentType]
                    request_details.path_args,
                )
            )

            # Disconnect and backup signals to avoid triggering them twice during create
            d_pre_save_signals = self._disconnect_signals(pre_save, config.model)
            d_post_save_signals = self._disconnect_signals(post_save, config.model)

            # Create the object, validate it, and check simple relations' permission
            created_obj: TDjangoModel = config.model(  # noqa: F841, SLF001
                **dict(simple_fields + simple_relations),
            )
            if clean_err := self._full_clean_obj(created_obj, request):
                return clean_err
            # Saving properties prior to saving the object will raise exception such as:
            # ValueError: save() prohibited to prevent data loss due to unsaved related object 'model_name'
            for attr_name, attr_value in property_fields:  # pyright: ignore [reportAny]
                setattr(created_obj, attr_name, attr_value)  # noqa: WPS220
            if simple_rel_err := self._check_simple_relations(
                created_obj, simple_relations, request_details
            ):
                return simple_rel_err

            # Update and check complex relations on the created object
            if complex_rel_err := self._update_and_check_complex_relations(
                created_obj,
                complex_relations,
                request_details,
            ):
                return complex_rel_err

            # Reconnect previously backed up save signals
            self._reconnect_signals(pre_save, config.model, d_pre_save_signals)
            self._reconnect_signals(post_save, config.model, d_post_save_signals)

            # Fully validate the created object as well as its related objects
            if clean_err := self._full_clean_obj(created_obj, request):
                return clean_err

            request_details.object = created_obj
            self.post_create(request_details)

            return 201, created_obj

        def _disconnect_signals(
            self, signal: ModelSignal, model_class: type[TDjangoModel]
        ) -> list[RegisteredReceiver]:
            """Disconnect the signals that are connected to the model."""
            model_sender_key = _make_id(model_class)  # pyright: ignore[reportUnknownVariableType]

            disconnected_signals: list[RegisteredReceiver] = []
            for (receiver_key, sender_key), receiver, _ in signal.receivers:  # pyright: ignore[reportAny]
                if sender_key != model_sender_key:
                    continue

                disconnected = signal.disconnect(  # pyright: ignore[reportUnknownMemberType]
                    dispatch_uid=receiver_key,  # pyright: ignore[reportAny]
                    sender=model_class,
                )
                if not disconnected:
                    msg = f"Failed to disconnect {receiver} from signal {signal}."
                    raise RuntimeError(msg)

                disconnected_signals.append(
                    RegisteredReceiver(
                        receiver_key=receiver_key,  # pyright: ignore[reportAny]
                        # Dereference the weak reference if needed.
                        receiver=receiver()  # type: ignore[arg-type]
                        if isinstance(receiver, weakref.ReferenceType)
                        else receiver,
                    )
                )

            return disconnected_signals

        def _reconnect_signals(
            self,
            signal: ModelSignal,
            model_class: type[TDjangoModel],
            registered_receivers: list[RegisteredReceiver],
        ) -> None:
            """Reconnect the signals that were disconnected by `_disconnect_signals`."""
            for receiver_key, receiver in registered_receivers:
                signal.connect(  # pyright: ignore[reportUnknownMemberType]
                    receiver=receiver,
                    sender=model_class,
                    dispatch_uid=receiver_key,  # type: ignore[arg-type]
                )

    return CreateEndpoint
