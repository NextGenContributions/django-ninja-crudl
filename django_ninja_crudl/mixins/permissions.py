"""Mixins for permissions check system."""

from abc import ABC
from typing import ClassVar, Generic

from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.types import RequestDetails, TDjangoModel_co


class PermissionMixin(Generic[TDjangoModel_co], ABC):
    """Permission check system mixin for the CRUDL API."""

    _permission_classes: ClassVar[list[type[BasePermission[TDjangoModel_co]]]] = []
    """List of permission classes to check."""

    def has_permission(
        self,
        request: RequestDetails[TDjangoModel_co],
    ) -> bool:
        """Check if the user has permission to perform the action."""
        # loop through all permission classes
        for permission_class in self._permission_classes:
            # create an instance of the permission class
            if not permission_class.__abstractmethods__:
                permission_instance = permission_class()
                # check if the user has permission
                if not permission_instance.has_permission(request):
                    return False
        return True

    def has_object_permission(
        self,
        request: RequestDetails[TDjangoModel_co],
    ) -> bool:
        """Check if the user has permission to perform the action on the object."""
        for permission_class in self._permission_classes:
            if not permission_class.__abstractmethods__:
                permission_instance = permission_class()
                if not permission_instance.has_object_permission(request):
                    return False
        return True

    def has_related_object_permission(
        self,
        request: RequestDetails[TDjangoModel_co],
    ) -> bool:
        """Check if the user has permission to perform the action on the related object."""
        for permission_class in self._permission_classes:
            if not permission_class.__abstractmethods__:
                permission_instance = permission_class()
                if not permission_instance.has_related_object_permission(request):
                    return False
        return True
