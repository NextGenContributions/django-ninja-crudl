"""Base class for the CrudlController which provides the needed feature methods."""

from abc import ABC
from copy import copy
from typing import Any, Generic, Literal, cast

from beartype import beartype
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.http import HttpRequest

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
from django_ninja_crudl.utils import validating_manager


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

    def _check_related_field_permission(
        self,
        obj: TDjangoModel,
        rel_field: str,
        rel_field_val: Any | None,  # noqa: ANN401  # pyright: ignore[reportExplicitAny]
        request_details: RequestDetails[TDjangoModel],
    ) -> tuple[Literal[404], ErrorSchema] | None:
        """Check if the object has permission for object(s) of the related field."""
        related_model_class = self._get_related_model(
            cast(type[TDjangoModel], obj._meta.model),  # noqa: SLF001
            rel_field,
        )

        # Related object(s) permission handling
        related_obj_pks = (  # pyright: ignore [reportUnknownVariableType]
            rel_field_val if isinstance(rel_field_val, list) else [rel_field_val]
        )
        for pk in related_obj_pks:  # pyright: ignore [reportUnknownVariableType]
            if perm_err := self._check_related_field_obj_permission(
                pk,  # pyright: ignore[reportUnknownArgumentType]
                related_model_class,
                request_details,
            ):
                return perm_err

        return None

    def _check_related_field_obj_permission(
        self,
        related_obj_pk: Any | None,  # noqa: ANN401  # pyright: ignore[reportExplicitAny]
        related_model_class: type[TDjangoModel],
        request_details: RequestDetails[TDjangoModel],
    ) -> tuple[Literal[404], ErrorSchema] | None:
        """Check if the related object exists and has permission."""
        # Check if the related object exists
        if related_obj_pk is None:
            return None

        try:
            related_obj = related_model_class._default_manager.get(  # noqa: SLF001
                pk=related_obj_pk,
            )
        except related_model_class.DoesNotExist:  # type: ignore[attr-defined]
            transaction.set_rollback(True)
            return self.get_404_error(request_details.request)

        # Check related object permission
        rd = copy(request_details)  # noqa: WPS220
        rd.related_model_class = related_model_class
        rd.related_object = related_obj
        if not self.has_related_object_permission(rd):
            transaction.set_rollback(True)
            return self.get_404_error(request_details.request)

        return None

    def _check_simple_relations(
        self,
        obj: TDjangoModel,
        relational_fields: list[DjangoFieldType],
        request_details: RequestDetails[TDjangoModel],
    ) -> tuple[Literal[404], ErrorSchema] | None:
        """Handle permission check for simple relations.

        Simple relations are ForeignKey and OneToOneField.
        """
        for rel_field, rel_field_val in relational_fields:  # pyright: ignore[reportAny]
            if perm_err := self._check_related_field_permission(
                obj,
                rel_field,
                rel_field_val,  # pyright: ignore[reportAny]
                request_details,
            ):
                return perm_err

        return None

    def _update_and_check_complex_relations(
        self,
        obj: TDjangoModel,
        relational_fields: list[DjangoFieldType],
        request_details: RequestDetails[TDjangoModel],
    ) -> tuple[Literal[404, 409], ErrorSchema] | None:
        """Handle updating and permission checking for complex relations.

        Complex relations are ManyToManyField, ManyToManyRel, ManyToOneRel, OneToOneRel.
        """
        for rel_field, rel_field_val in relational_fields:  # pyright: ignore[reportAny]
            # Handle permission check for complex relations
            if perm_err := self._check_related_field_permission(
                obj,
                rel_field,
                rel_field_val,  # pyright: ignore[reportUnknownArgumentType]
                request_details,
            ):
                return perm_err

            # Perform the update
            try:
                update_rel = (
                    self._update_many_rel
                    if isinstance(rel_field_val, list)
                    else self._update_one_to_one_rel
                )
                update_rel(obj, rel_field, rel_field_val)
            except IntegrityError:
                transaction.set_rollback(True)  # noqa: WPS220
                return self.get_409_error(request_details.request)

        return None

    def _update_many_rel(
        self,
        obj: TDjangoModel,
        rel_field: str,
        rel_field_val: Any,  # noqa: ANN401  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        """Handle ManyToManyField, ManyToManyRel, ManyToOneRel."""
        related_model_class = self._get_related_model(
            cast(type[TDjangoModel], obj._meta.model),  # noqa: SLF001
            rel_field,
        )
        related_objs = related_model_class._default_manager.filter(  # noqa: SLF001
            pk__in=rel_field_val,
        )
        getattr(obj, rel_field).set(related_objs)  # pyright: ignore[reportAny]

    def _update_one_to_one_rel(
        self,
        obj: TDjangoModel,
        rel_field: str,
        rel_field_val: Any,  # noqa: ANN401  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        """Update OneToOneRel."""
        # setattr(obj, f"{field}_pk", pk)) does not work for "OneToOneRel"
        # and save() must be called on 'related_obj' instead of 'obj'
        related_model_class = self._get_related_model(
            cast(type[TDjangoModel], obj._meta.model),  # noqa: SLF001
            rel_field,
        )
        related_obj: TDjangoModel | None
        if rel_field_val is None:
            # Removing the relation, if exists
            related_obj = cast(TDjangoModel | None, getattr(obj, rel_field, None))
            if related_obj:
                setattr(obj, rel_field, None)
                related_obj.save()
        else:
            # Updating the relation
            related_obj = related_model_class._default_manager.get(pk=rel_field_val)  # noqa: SLF001
            setattr(obj, rel_field, related_obj)
            related_obj.save()

    def _full_clean_obj(
        self, obj: models.Model, request: HttpRequest
    ) -> tuple[Literal[409], ErrorSchema] | None:
        """Perform full_clean() on the object."""
        # TODO(phuongfi91): check from related objects perspective
        #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
        try:
            # TODO(phuongfi91): should this be also done in a through model?
            #  (if the manytomanyfield has a through model set)
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            with validating_manager(obj._meta.model):
                obj.save()
        except (IntegrityError, ValidationError) as error:
            # revert the transaction
            transaction.set_rollback(True)
            return self.get_409_error(request, exception=error)
        return None

    def _get_path_args(self, kwargs: RequestParams) -> PathArgs:
        return kwargs["path_args"].model_dump() if "path_args" in kwargs else {}
