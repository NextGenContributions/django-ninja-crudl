"""Mixins for soft-delete handling."""

# pyright: reportUnusedParameter=false
from abc import ABC
from typing import Generic

from django.db.models import Model, QuerySet

from django_ninja_crudl.types import RequestDetails, TDjangoModel


class SoftDeleteMixin(ABC, Generic[TDjangoModel]):
    """Mixin for soft-delete handling."""

    def soft_delete(
        self,
        qs: QuerySet[Model],
        request_details: RequestDetails[TDjangoModel],
        using_db: str,
    ) -> None:
        """Define how to soft-delete the given queryset of (related) objects.

        This must be implemented in CRUDL controller subclass if soft-delete is enabled.

        Args:
            qs: The queryset of (related) objects to soft-delete.
            request_details: The details of the request.
            using_db: The database alias to use.
        """
        msg = "soft_delete method must be implemented in subclass."
        raise NotImplementedError(msg)
