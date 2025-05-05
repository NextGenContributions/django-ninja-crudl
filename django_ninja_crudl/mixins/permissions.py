"""Mixins for permissions check system."""

from abc import ABC
from collections.abc import Callable
from typing import ClassVar, Generic

from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.types import RequestDetails, TDjangoModel


class PermissionMixin(Generic[TDjangoModel], ABC):
    """Permission check system mixin for the CRUDL API."""

    _permission_classes: ClassVar[list[type[BasePermission[TDjangoModel]]]] = []  # type: ignore[misc]
    """List of permission classes to check."""

    def _check_all(self, call: Callable[[BasePermission[TDjangoModel]], bool]) -> bool:
        """Go through all permission classes and check if the user has permission."""
        for permission_class in self._permission_classes:
            if not permission_class.__abstractmethods__:
                permission_instance = permission_class()
                if not call(permission_instance):
                    return False
        return True

    def is_authenticated(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user is authenticated."""
        return self._check_all(lambda perm: perm.is_authenticated(request))

    def has_permission(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user has permission to perform the action."""
        return self._check_all(lambda perm: perm.has_permission(request))

    def has_object_permission(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user has permission to perform the action on the object."""
        return self._check_all(lambda perm: perm.has_object_permission(request))

    def has_related_object_permission(
        self, request: RequestDetails[TDjangoModel]
    ) -> bool:
        """Check if the user has permission to perform action on the related object."""
        return self._check_all(lambda perm: perm.has_related_object_permission(request))
