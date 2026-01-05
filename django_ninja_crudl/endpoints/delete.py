"""CRUDL API base class."""

import logging
from abc import ABC
from typing import Literal, Unpack

from django.db import IntegrityError, transaction
from django.http import HttpRequest
from ninja_extra import http_delete, status

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

logger = logging.getLogger(__name__)


def get_delete_endpoint(config: CrudlConfig[TDjangoModel]) -> type:
    """Create the delete endpoint class for the CRUDL operations."""

    class DeleteEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):  # pyright: ignore [reportGeneralTypeIssues]
        @http_delete(
            path=config.delete_path,
            operation_id=config.delete_operation_id,
            url_name=config.delete_operation_id,
            response={
                status.HTTP_204_NO_CONTENT: None,
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
                status.HTTP_409_CONFLICT: Error409ConflictSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
        )
        @transaction.atomic
        @replace_path_args_annotation(config.delete_path, config.model)
        def delete(
            self,
            request: HttpRequest,
            **kwargs: Unpack[RequestParams],
        ) -> (
            tuple[Literal[401, 403, 404, 409], ErrorSchema] | tuple[Literal[204], None]
        ):
            """Delete the object by id."""
            request_details = RequestDetails[TDjangoModel](
                action="delete",
                request=request,
                path_args=self._get_path_args(kwargs),
                model_class=config.model,
            )
            if not self.is_authenticated(request_details):
                return self.get_401_error(request)
            if not self.has_permission(request_details):
                return self.get_403_error(request)

            obj = (
                self.get_pre_filtered_queryset(config.model, request_details.path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_delete(request_details))
                .first()
            )
            if obj is None:
                return self.get_404_error(request)
            request_details.object = obj
            if not self.has_object_permission(request_details):
                return self.get_404_error(request)

            self.pre_delete(request_details)
            try:
                self.delete_obj(obj, request_details, mode=config.delete_options.mode)
            except IntegrityError as exc:
                # This should cover also ProtectedError, RestrictedError enforced by
                # PROTECT/RESTRICT model constraints
                return self.get_409_error(request, exception=exc)
            self.post_delete(request_details)
            return 204, None

        def delete_obj(
            self,
            obj: TDjangoModel,
            request_details: RequestDetails[TDjangoModel],
            *,
            mode: Literal["hard", "soft"] = "hard",
        ) -> None:
            """Delete the collected objects according to the specified mode."""
            logger.debug("Deleting object %s with delete mode: %s", obj, mode)

            if mode == "hard":
                obj.delete()
                return

            # "soft" delete
            self._soft_delete_obj(obj, request_details)

    return DeleteEndpoint
