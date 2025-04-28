"""CRUDL API base class."""

import logging
from abc import ABC
from typing import TYPE_CHECKING, Literal, Unpack

from django.db import transaction
from django.http import HttpRequest
from ninja_extra import http_put, status

from django_ninja_crudl import CrudlConfig
from django_ninja_crudl.base import CrudlBaseMethodsMixin
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

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


def get_update_endpoint(config: CrudlConfig[TDjangoModel]) -> type | None:
    """Create the update endpoint class for the CRUDL operations."""
    if not config.update_schema:
        return None

    update_schema: type[BaseModel] = config.update_schema

    class UpdateEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):  # pyright: ignore [reportGeneralTypeIssues]
        """Base class for the CRUDL API."""

        @http_put(
            path=config.update_path,
            operation_id=config.update_operation_id,
            url_name=config.update_operation_id,
            response={
                status.HTTP_200_OK: update_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_409_CONFLICT: Error409ConflictSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            by_alias=True,
        )
        @transaction.atomic
        @replace_path_args_annotation(config.update_path, config.model)
        def update(
            self,
            request: HttpRequest,
            payload: update_schema,  # type: ignore[valid-type]
            **kwargs: Unpack[RequestParams],
        ) -> tuple[Literal[401, 403, 404, 409], ErrorSchema] | TDjangoModel:
            """Update an object."""
            request_details = RequestDetails[TDjangoModel](
                action="put",
                request=request,
                schema=update_schema,
                path_args=self._get_path_args(kwargs),
                payload=payload,
                model_class=config.model,
            )
            if not self.is_authenticated(request_details):
                return self.get_401_error(request)
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            obj = (
                self.get_pre_filtered_queryset(config.model, request_details.path_args)
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

            simple_fields, relational_fields = self._get_fields_to_set(
                config.model, payload
            )

            def update() -> None:
                nonlocal obj
                with validating_manager(config.model):  # noqa: WPS220
                    # TODO(phuongfi91): should we use validating_manager later as well?
                    for attr_name, attr_value in simple_fields:
                        setattr(obj, attr_name, attr_value)  # noqa: WPS220
                    obj.save()  # pyright: ignore [reportOptionalMemberAccess]

            if update_err := self._try(update, request):
                return update_err

            # Update complex relations on the created object
            if rel_err := self._update_complex_relations(
                obj,
                relational_fields,
                request,
                request_details,
            ):
                return rel_err

            # Fully validate the created object as well as its related objects
            if clean_err := self._full_clean_obj(obj, request):
                return clean_err

            self.post_update(request_details)
            return obj

    return UpdateEndpoint
