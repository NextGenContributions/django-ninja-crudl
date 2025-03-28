"""Permissions for CRUDL views."""

from abc import ABC, abstractmethod
from typing import Generic

from beartype import beartype

from django_ninja_crudl.types import RequestDetails, TDjangoModel


@beartype
class BasePermission(Generic[TDjangoModel], ABC):
    """Base class for permissions."""

    @abstractmethod
    def has_permission(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user has permission to perform the action."""
        return False

    @abstractmethod
    def has_object_permission(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user has permission to perform the action on the object."""
        return False

    @abstractmethod
    def has_related_object_permission(
        self, request: RequestDetails[TDjangoModel]
    ) -> bool:
        """Check if the user has permission to perform the action on the related object."""
        return False
