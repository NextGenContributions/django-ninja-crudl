"""Base class for the CrudlController which provides the needed feature methods."""

from abc import ABC
from collections.abc import Callable
from typing import Generic, Literal

from beartype import beartype
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.http import HttpRequest
from pydantic import BaseModel

from django_ninja_crudl.errors import (
    ErrorHandlerMixin,
    ErrorSchema,
)
from django_ninja_crudl.mixins import (
    FiltersMixin,
    HooksMixin,
    PermissionMixin,
    UtilitiesMixin,
)
from django_ninja_crudl.types import (
    DjangoFieldType,
    PathArgs,
    RequestDetails,
    RequestParams,
    TDjangoModel,
)
from django_ninja_crudl.utils import get_model_field


@beartype
class CrudlBaseMethodsMixin(  # noqa: WPS215 too many base classes
    Generic[TDjangoModel],
    ErrorHandlerMixin,
    FiltersMixin[TDjangoModel],
    HooksMixin[TDjangoModel],
    PermissionMixin[TDjangoModel],
    UtilitiesMixin[TDjangoModel],
    ABC,
):
    """Provide base feature methods for the CrudlController."""

    def _get_fields_to_set(
        self,
        model_class: type[TDjangoModel],
        payload: BaseModel,
    ) -> tuple[list[DjangoFieldType], list[DjangoFieldType]]:
        """Get the fields to set for the create operation."""
        obj_fields_to_set: list[DjangoFieldType] = []
        # TODO(phuongfi91): renaming m2m_fields_to_set?
        #  https://github.com/NextGenContributions/django-ninja-crudl/issues/11
        m2m_fields_to_set: list[DjangoFieldType] = []

        for field, field_value in payload.model_dump().items():  # pyright: ignore[reportAny]
            field_type = get_model_field(model_class, field)
            if isinstance(
                field_type,
                models.ManyToManyField
                | models.ManyToManyRel
                | models.ManyToOneRel
                | models.OneToOneRel,
            ):
                m2m_fields_to_set.append((field, field_value))
            else:
                # Handle foreign key fields:
                if isinstance(  # noqa: WPS220
                    field_type, models.ForeignKey
                ) and not field.endswith("_id"):
                    field_name = f"{field}_id"

                # TODO(phuongfi91): what about OneToOneField?

                else:  # Non-relational fields
                    field_name = field

                obj_fields_to_set.append((field_name, field_value))
        return m2m_fields_to_set, obj_fields_to_set

    def _try(
        self, handler: Callable[..., None], request: HttpRequest
    ) -> tuple[Literal[409], ErrorSchema] | None:  # noqa: WPS432
        try:
            handler()
        except IntegrityError as integrity_error:
            transaction.set_rollback(True)
            return self.get_409_error(request, exception=integrity_error)
        except ValidationError as validation_error:
            transaction.set_rollback(True)
            return self.get_409_error(request, exception=validation_error)

        return None

    def _update_m2m_relationships(
        self,
        obj: TDjangoModel,
        m2m_fields_to_set: list[DjangoFieldType],
        request: HttpRequest,
        request_details: RequestDetails[TDjangoModel],
    ) -> tuple[Literal[404, 409], ErrorSchema] | None:
        """Handle many-to-many relationships for an object."""
        for m2m_field, m2m_field_value in m2m_fields_to_set:  # pyright: ignore[reportAny]
            related_model_class = self._get_related_model(
                obj._meta.model,  # noqa: SLF001
                m2m_field,
            )

            if isinstance(m2m_field_value, list):
                for m2m_field_value_item in m2m_field_value:
                    try:
                        related_obj = related_model_class._default_manager.get(  # noqa: SLF001
                            id=m2m_field_value_item,
                        )
                    except related_model_class.DoesNotExist:  # type: ignore[attr-defined]
                        transaction.set_rollback(True)
                        return self.get_404_error(request)

                    request_details_related = request_details  # noqa: WPS220
                    request_details_related.related_model_class = related_model_class
                    request_details_related.related_object = related_obj
                    if not self.has_related_object_permission(
                        request_details_related,
                    ):
                        transaction.set_rollback(True)
                        return self.get_404_error(request)
            else:
                related_obj = related_model_class._default_manager.get(  # noqa: SLF001
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

        return None

    def _full_clean_obj(
        self, obj: models.Model, request: HttpRequest
    ) -> tuple[Literal[409], ErrorSchema] | None:
        """Perform full_clean() on the object."""
        # TODO(phuongfi91): check from related objects perspective
        try:
            # TODO(phuongfi91): should this be also done in a through model?
            #  (if the manytomanyfield has a through model set)
            obj.full_clean()
        except ValidationError as validation_error:
            # revert the transaction
            transaction.set_rollback(True)
            return self.get_409_error(request, exception=validation_error)

        return None

    def _get_path_args(self, kwargs: RequestParams) -> PathArgs:
        return kwargs["path_args"].model_dump() if "path_args" in kwargs else {}
