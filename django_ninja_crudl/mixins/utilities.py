"""Utility methods for the CRUDL classes."""

from typing import Generic, Literal, cast
from uuid import UUID

from django.db import models
from django.db.models import (
    Manager,
    QuerySet,
)

from django_ninja_crudl.types import (
    PathArgs,
    RequestDetails,
    TDjangoModel,
)
from django_ninja_crudl.utils import get_model_field


class UtilitiesMixin(Generic[TDjangoModel]):
    """Utility methods for the CRUDL classes."""

    def _get_related_model(
        self, model_class: type[TDjangoModel], field_name: str
    ) -> type[TDjangoModel]:
        """Return the related model class for a field name."""
        field = get_model_field(model_class, field_name)
        related_model = cast(
            # TODO(phuongfi91): django-stubs also return 'Any' for 'GenericForeignKey'
            #  which should not be possible?
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            type[TDjangoModel] | Literal["self"] | None,
            field.related_model,
        )

        if related_model == "self":
            related_model = model_class

        if related_model is not None:
            return related_model

        # 'related_model' is None
        msg = f"Field name '{field_name}' and type '{type(field)}' is not a relation."
        raise ValueError(msg)

    def get_model_filter_args(
        self,
        model_class: type[TDjangoModel],
        path_args: PathArgs | None,
    ) -> dict[str, str | int | float | UUID]:
        """Filter out the keys that are not fields of the model."""
        if path_args is None:
            return {}
        return {k: v for k, v in path_args.items() if getattr(model_class, k, None)}

    def get_pre_filtered_queryset(
        self,
        model_class: type[TDjangoModel],
        path_args: PathArgs | None,
    ) -> QuerySet[TDjangoModel]:
        """Return a queryset that is filtered by params from the path query."""
        model_filters = self.get_model_filter_args(model_class, path_args)
        return self.get_queryset(model_class).filter(**model_filters)

    def get_queryset(self, model_class: type[TDjangoModel]) -> "Manager[TDjangoModel]":
        """Return the model's manager."""
        return model_class._default_manager  # noqa: SLF001 pylint: disable=protected-access

    # TODO(phuongfi91): This method is not used anywhere, what is this used for?
    #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
    def get_filtered_queryset_for_related_model(
        self,
        request: RequestDetails[TDjangoModel],
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
