"""CRUDL API base class."""

import logging
from abc import ABC
from typing import Any, Literal, Unpack

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
    RequestDetails,
    RequestParams,
)
from django_ninja_crudl.utils import (
    get_model_field,
    replace_path_args_annotation,
    validating_manager,
)

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


def get_partial_update_endpoint(config: CrudlConfig[Model]) -> type:
    """Create the partial update endpoint class for the CRUDL operations."""

    class PartialUpdateEndpoint(CrudlBaseMethodsMixin[Model], ABC):  # pyright: ignore [reportGeneralTypeIssues]
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
        @replace_path_args_annotation(config.update_path, config.model)
        def patch(
            self,
            request: HttpRequest,
            payload: config.partial_update_schema,  # type: ignore[name-defined]
            **kwargs: Unpack[RequestParams],
        ) -> tuple[Literal[403, 404, 409], ErrorSchema] | Model:
            """Partial update an object."""
            request_details = RequestDetails[Model](
                action="patch",
                request=request,
                schema=config.partial_update_schema,  # pyright: ignore[reportPossiblyUnboundVariable]
                path_args=self._get_path_args(kwargs),
                payload=payload,  # pyright: ignore[reportUnknownArgumentType]
                model_class=config.model,
            )
            if not self.has_permission(request_details):
                return self.get_403_error(request)  # noqa: WPS220
            obj: Model | None = (
                self.get_pre_filtered_queryset(config.model, request_details.path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_update(request_details))
                .first()
            )
            if obj is None:
                return self.get_404_error(request)  # noqa: WPS220
            request_details.object = obj
            if not self.has_object_permission(request_details):
                return self.get_404_error(request)  # noqa: WPS220
            self.pre_patch(request_details)

            ##################### begin of madness
            obj_fields_to_set: list[tuple[str, Any]] = []  # pyright: ignore[reportExplicitAny]
            m2m_fields_to_set: list[tuple[str, Any]] = []  # pyright: ignore[reportExplicitAny]

            # TODO(phuongfi91): payload is a dict here, no model_dump() method, unlike
            #  with POST in update.py
            # for field, field_value in payload.model_dump().items():
            for field, field_value in payload.items():
                if isinstance(
                    get_model_field(config.model, field),
                    ManyToManyField | ManyToManyRel | ManyToOneRel | OneToOneRel,
                ):
                    m2m_fields_to_set.append((field, field_value))  # noqa: WPS220
                else:
                    # Handle foreign key fields:
                    if isinstance(  # noqa: WPS220
                        get_model_field(config.model, field),
                        ForeignKey,
                    ) and not field.endswith("_id"):
                        field_name = f"{field}_id"  # noqa: WPS220
                    else:  # Non-relational fields
                        field_name = field  # noqa: WPS220

                    obj_fields_to_set.append((field_name, field_value))  # noqa: WPS220
            try:
                with validating_manager(config.model):  # noqa: WPS220
                    # TODO(phuongfi91):
                    for attr_name, attr_value in obj_fields_to_set:
                        setattr(obj, attr_name, attr_value)  # noqa: WPS220
                    obj.save()
            # if integrity error, return 409
            except IntegrityError as integrity_error:
                transaction.set_rollback(True)
                return self.get_409_error(request, exception=integrity_error)

            for m2m_field, m2m_field_value in m2m_fields_to_set:  # pyright: ignore[reportAny]
                related_model_class = self._get_related_model(config.model, m2m_field)

                if isinstance(m2m_field_value, list):  # noqa: WPS220
                    for m2m_field_value_item in m2m_field_value:
                        related_obj = related_model_class.objects.get(
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
                    # TODO(phuongfi91): related_obj is unused
                    related_obj = related_model_class.objects.get(
                        id=m2m_field_value,
                    )

                    if not self.has_related_object_permission(request_details):
                        transaction.set_rollback(True)
                        return self.get_404_error(request)

                try:
                    # TODO(phuongfi91): OneToOneField/Rel does not have set()
                    #  and would raise IntegrityError
                    getattr(obj, m2m_field).set(m2m_field_value)
                except IntegrityError:
                    transaction.set_rollback(True)  # noqa: WPS220
                    return self.get_409_error(request)

            # Perform full_clean() on the created object and raise an exception if it fails
            try:
                # TODO(phuongfi91):
                obj.full_clean()  # noqa: WPS220
            except ValidationError as validation_error:
                # revert the transaction
                transaction.set_rollback(True)  # noqa: WPS220
                return self.get_409_error(request, exception=validation_error)

            ############### end of madness

            # TODO(phuongfi91): remove this after completing the full solution above ^
            # for attr_name, attr_value in payload.items():
            #     try:
            #         setattr(obj, attr_name, attr_value)
            #     except TypeError as e:
            #         msg = (
            #             "Direct assignment to the forward side of a many-to-many set "
            #             "is prohibited."
            #         )
            #         if msg in str(e):
            #             m2m_manager: ManyRelatedManager[Model] = getattr(obj, attr_name)
            #             m2m_manager.set(attr_value)
            #         else:
            #             raise
            # obj.save()

            self.post_patch(request_details)
            return obj

    return PartialUpdateEndpoint
