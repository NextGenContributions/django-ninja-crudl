"""CRUDL API base class."""

import logging
from abc import ABC
from typing import TYPE_CHECKING, Literal, Unpack

from django.db import transaction
from django.http import HttpRequest
from ninja_extra import http_patch, status

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
)

if TYPE_CHECKING:
    from pydantic import BaseModel

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


def get_partial_update_endpoint(config: CrudlConfig[TDjangoModel]) -> type | None:
    """Create the partial update endpoint class for the CRUDL operations."""
    if not config.partial_update_schema:
        return None

    partial_update_schema: type[BaseModel] = config.partial_update_schema

    class PartialUpdateEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):  # pyright: ignore [reportGeneralTypeIssues]
        @http_patch(
            path=config.update_path,
            operation_id=config.partial_update_operation_id,
            url_name=config.partial_update_operation_id,
            response={
                status.HTTP_200_OK: partial_update_schema,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_409_CONFLICT: Error409ConflictSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            exclude_unset=True,
            by_alias=True,
        )
        @transaction.atomic
        @replace_path_args_annotation(config.update_path, config.model)
        def patch(
            self,
            request: HttpRequest,
            payload: partial_update_schema,  # type: ignore[valid-type]
            **kwargs: Unpack[RequestParams],
        ) -> tuple[Literal[401, 403, 404, 409], ErrorSchema] | TDjangoModel:
            """Partial update an object."""
            request_details = RequestDetails[TDjangoModel](
                action="patch",
                request=request,
                schema=partial_update_schema,
                path_args=self._get_path_args(kwargs),
                payload=payload,  # pyright: ignore [reportUnknownArgumentType]
                model_class=config.model,
            )
            if not self.is_authenticated(request_details):
                return self.get_401_error(request)
            if not self.has_permission(request_details):
                return self.get_403_error(request)
            obj: TDjangoModel | None = (
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
            self.pre_patch(request_details)

            simple_fields, simple_relations, complex_relations = (
                self._get_fields_to_set(config.model, payload)  # pyright: ignore [reportUnknownArgumentType]
            )

            # Update the object, validate it, and check simple relations' permission
            for attr_name, attr_value in simple_fields + simple_relations:  # pyright: ignore [reportAny]
                setattr(obj, attr_name, attr_value)  # noqa: WPS220
            # if clean_err := self._full_clean_obj(obj, request):
            #     return clean_err
            if simple_rel_err := self._check_simple_relations(
                obj, simple_relations, request_details
            ):
                return simple_rel_err

            # Update and check complex relations on the created object
            if rel_err := self._update_and_check_complex_relations(
                obj,
                complex_relations,
                request_details,
            ):
                return rel_err

            # Fully validate the created object as well as its related objects
            if clean_err := self._full_clean_obj(obj, request):
                return clean_err

            self.post_patch(request_details)
            return obj

    return PartialUpdateEndpoint
