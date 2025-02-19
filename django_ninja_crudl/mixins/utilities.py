"""Utility methods for the CRUDL classes."""

from typing import Any, Generic, cast
from uuid import UUID

from django.db import models
from django.db.models import (
    ForeignObjectRel,
    Manager,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
    QuerySet,
)

from django_ninja_crudl.types import PathArgs, RequestDetails, TDjangoModel_co


class UtilitiesMixin(Generic[TDjangoModel_co]):
    """Utility methods for the CRUDL classes."""

    def _get_related_model(
        self, model_class: type[TDjangoModel_co], field_name: str
    ) -> Model:
        """Return the related model class for a field name."""
        field = model_class._meta.get_field(field_name)  # noqa: SLF001, WPS437
        if isinstance(field, ForeignObjectRel):
            return field.related_model
        if isinstance(field, OneToOneRel):
            return cast(type[Model], field.related_model)
        if isinstance(field, ManyToManyRel):
            return cast(type[Model], field.related_model)
        if isinstance(field, ManyToOneRel):
            return cast(type[Model], field.related_model)
        if isinstance(field, ManyToManyField):
            return cast(type[Model], field.related_model)

        msg = (
            f"Field name '{field_name}' and type '{type(field)}' " "is not a relation."
        )
        raise ValueError(msg)

    def get_model_filter_args(
        self,
        model_class: type[Model],
        path_args: dict[str, Any] | None,
    ) -> dict[str, str | int | float | UUID]:
        """Filter out the keys that are not fields of the model."""
        if path_args is None:
            return {}
        return {k: v for k, v in path_args.items() if getattr(model_class, k, None)}

    def get_pre_filtered_queryset(
        self,
        path_args: PathArgs,
    ) -> QuerySet[Model]:
        """Return a queryset that is filtered by params from the path query."""
        model_filters = self.get_model_filter_args(path_args)
        return self.get_queryset().filter(**model_filters)

    def get_queryset(self, model_class: type[Model]) -> "Manager[Model]":
        """Return the model's manager."""
        return model_class._default_manager  # noqa: SLF001, WPS437 pylint: disable=protected-access

    def get_filtered_queryset_for_related_model(
        self,
        request: RequestDetails,
        field_name: str,
    ) -> models.Q:
        """Get filtered queryset for related model based on custom conditions."""
        # Get the appropriate filtering method based on the field name
        filter_method_name = f"get_related_filter_for_field_{field_name}"
        filter_method = getattr(self, filter_method_name, None)
        if not callable(filter_method):
            filter_not_callable_msg = (
                f"Filter method {filter_method_name} is not callable."
            )
            raise TypeError(filter_not_callable_msg)

        result = filter_method(request, field_name)
        if not isinstance(result, models.Q):
            result_type = type(result)
            expected_type_not_q_msg = f"Expected return type 'Q', got {result_type}."
            raise TypeError(expected_type_not_q_msg)
        return result
