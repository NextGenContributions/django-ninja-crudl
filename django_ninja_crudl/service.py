"""CRUDL API base class."""

import logging
from abc import ABC
from enum import Enum, IntEnum
from typing import Any, Generic, Literal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
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
from ninja_extra import (
    api_controller,
)
from pydantic import BaseModel

from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.config import CrudlConfig
from django_ninja_crudl.errors.schemas import (
    ErrorSchema,
)
from django_ninja_crudl.model_utils import get_pydantic_fields
from django_ninja_crudl.types import PathArgs, RequestDetails, TDjangoModel_co
from django_ninja_crudl.utils import validating_manager

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)


@api_controller
class CreateEndpoint(
    Generic[TDjangoModel_co], CrudlBaseMethodsMixin[TDjangoModel_co], ABC
):
    """Base class for the CRUDL API."""

    config: CrudlConfig[TDjangoModel_co]

    def create_impl(
        self,
        request: HttpRequest,
        payload: BaseModel,
        **path_args: PathArgs,
    ) -> tuple[Literal[403, 404, 409], ErrorSchema] | tuple[Literal[201], Model]:
        """Create a new object."""
        request_details = RequestDetails[TDjangoModel_co](
            action="create",
            request=request,
            schema=self.config.create_schema,
            path_args=path_args,
            payload=payload,
            model_class=self.config.model,
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
                self.config.model._meta.get_field(field),  # noqa: SLF001, WPS437
                ManyToManyField | ManyToManyRel | ManyToOneRel | OneToOneRel,
            ):
                m2m_fields_to_set.append((field, field_value))
            else:
                # Handle foreign key fields:
                if isinstance(  # noqa: WPS220, WPS337
                    self.config.model._meta.get_field(field),  # noqa: SLF001, WPS437
                    ForeignKey,
                ) and not field.endswith("_id"):
                    field_name = f"{field}_id"
                else:  # Non-relational fields
                    field_name = field

                obj_fields_to_set.append((field_name, field_value))
        try:
            with validating_manager(self.config.model):
                created_obj: Model = self.config.model._default_manager.create(  # noqa: SLF001
                    **dict(obj_fields_to_set),
                )
        # if integrity error, return 409
        except IntegrityError as integrity_error:
            transaction.set_rollback(True)
            return self.get_409_error(request, exception=integrity_error)

        for m2m_field, m2m_field_value in m2m_fields_to_set:  # pyright: ignore[reportAny]
            related_model_class = self._get_related_model(m2m_field)  # pyright: ignore[reportPrivateUsage]

            if isinstance(m2m_field_value, list):
                for m2m_field_value_item in m2m_field_value:
                    related_obj = related_model_class._default_manager.get(
                        id=m2m_field_value_item,
                    )
                    request_details_related = request_details  # noqa: WPS220
                    request_details_related.related_model_class = related_model_class
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


class GetOneEndpoint:
    def get_by_id_impl(
        self,
        request: HttpRequest,
        **path_args: PathArgs,
    ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
        """Retrieve an object."""
        request_details = RequestDetails[TDjangoModel_co](
            action="get_one",
            request=request,
            schema=self.config.get_one_schema,
            path_args=path_args,
            model_class=self.config.model,
        )
        if not self.has_permission(request_details):
            return self.get_403_error(request)

        obj = (
            self.get_pre_filtered_queryset(path_args)
            .filter(self.get_base_filter(request_details))
            .filter(self.get_filter_for_get_one(request_details))
            .first()
        )
        if obj is None:
            return self.get_404_error(request)
        request_details.object = obj
        if not self.has_object_permission(request_details):
            return self.get_404_error(request)
        return obj

    def update_impl(
        self,
        request: HttpRequest,
        payload: BaseModel,
        **path_args: PathArgs,
    ) -> tuple[Literal[403, 404], ErrorSchema] | TDjangoModel_co:
        """Update an object."""
        request_details = RequestDetails[TDjangoModel_co](
            action="put",
            request=request,
            schema=self.config.update_schema,
            path_args=path_args,
            payload=payload,
            model_class=self.config.model,
        )
        if not self.has_permission(request_details):
            return self.get_403_error(request)
        obj = (
            self.get_pre_filtered_queryset(path_args)
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

        for attr_name, attr_value in payload.model_dump().items():
            setattr(obj, attr_name, attr_value)
        obj.save()
        self.post_update(request_details)
        return obj

    def partial_update_impl(
        self,
        request: HttpRequest,
        payload: BaseModel,
        **path_args: PathArgs,
    ) -> tuple[Literal[403, 404], ErrorSchema] | TDjangoModel_co:
        """Partial update an object."""
        request_details = RequestDetails[TDjangoModel_co](
            action="patch",
            request=request,
            schema=self.config.partial_update_schema,
            path_args=path_args,
            payload=payload,
            model_class=self.config.model,
        )
        if not self.has_permission(request_details):
            return self.get_403_error(request)  # noqa: WPS220
        obj = (
            self.get_pre_filtered_queryset(path_args)
            .filter(self.get_base_filter(request_details))
            .filter(self.get_filter_for_update(request_details))
            .first()
        )
        if obj is None:
            return self.get_404_error(request)
        request_details.object = obj
        if not self.has_object_permission(request_details):
            return self.get_404_error(request)

        for attr_name, attr_value in payload.model_dump().items():
            setattr(obj, attr_name, attr_value)
        obj.save()
        self.post_patch(request_details)
        return obj

    def delete_impl(
        self,
        request: HttpRequest,
        **path_args: PathArgs,
    ) -> tuple[Literal[403, 404], ErrorSchema] | tuple[Literal[204], None]:
        """Delete the object by id."""
        request_details = RequestDetails[TDjangoModel_co](
            action="delete",
            request=request,
            path_args=path_args,
            model_class=self.config.model,
        )
        if not self.has_permission(request_details):
            return self.get_403_error(request)

        obj = (
            self.get_pre_filtered_queryset(path_args)
            .filter(self.get_filter_for_delete(request_details))
            .first()
        )
        if obj is None:
            return self.get_404_error(request)
        request_details.object = obj
        if not self.has_object_permission(request_details):
            return self.get_404_error(request)
        self.pre_delete(request_details)
        _ = obj.delete()
        self.post_delete(request_details)
        return 204, None

    def list_impl(  # noqa: WPS210
        self,
        request: HttpRequest,
        response: HttpResponse,
        **path_args: PathArgs,
    ) -> tuple[int, ErrorSchema] | models.Manager[TDjangoModel_co]:
        """List all objects."""
        request_details = RequestDetails[TDjangoModel_co](
            action="list",
            request=request,
            path_args=path_args,
            model_class=self.config.model,
        )

        if not self.has_permission(request_details):
            return self.get_403_error(request)  # noqa: WPS220

        qs = (
            self.get_pre_filtered_queryset(path_args)
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

        for field_name in self.config.list_schema.model_fields:
            attr = getattr(self.model_class, field_name, None)

            # Skip @property methods here
            if attr and isinstance(attr, property):
                property_fields.append(field_name)
                # TODO: Implement a way to avoid N+1 queries when using @property methods
                logger.debug(
                    "Detected use of @property method %s of the model %s in"
                    " list_fields definition which"
                    " may cause N+1 queries and cause performance degradation.",
                    field_name,
                    self.model_class,
                )
                return qs

            django_field = self.config.model._meta.get_field(field_name)  # noqa: SLF001
            if isinstance(
                django_field,
                OneToOneField | ForeignKey,
            ):
                related_models.append(field_name)  # noqa: WPS220
                related_fields.extend(  # noqa: WPS220
                    get_pydantic_fields(
                        self.config.list_schema,
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
                        self.config.list_schema,
                        field_name,
                    ),
                )
                # related_models.append(f"{field_name}__id")

        non_related_fields: list[str] = [
            field_name
            for field_name in self.list_schema.model_fields
            if field_name not in related_models + many_to_many_models + property_fields
        ]

        all_fields: list[str] = non_related_fields + related_fields

        qs = qs.select_related(*related_models).prefetch_related(
            *many_to_many_models,
        )  # To avoid N+1 queries
        return qs.values(*all_fields)
