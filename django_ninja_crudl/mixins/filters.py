"""Mixins for filtering data."""

from abc import ABC, abstractmethod
from typing import Generic

from django.db.models import Q  # noqa: WPS347

from django_ninja_crudl.types import RequestDetails, TDjangoModel_co


class FiltersMixin(Generic[TDjangoModel_co], ABC):
    """Mixin for filtering data."""

    @abstractmethod
    def get_base_filter(
        self,
        request: RequestDetails[TDjangoModel_co],
    ) -> Q:
        """Return the base filter for all types of operations."""
        raise NotImplementedError

    def get_filter_for_list(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> Q:
        """Return the filter specific to the list operation."""
        raise NotImplementedError

    def get_filter_for_update(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> Q:
        """Return the filter specific to the update operation."""
        raise NotImplementedError

    def get_filter_for_delete(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> Q:
        """Return the filter specific to the delete operation."""
        raise NotImplementedError

    def get_filter_for_get_one(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> Q:
        """Return the filter specific to the get one operation."""
        raise NotImplementedError
