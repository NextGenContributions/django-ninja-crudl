"""Base classes for the CRUDL API."""

from abc import abstractmethod
from typing import ClassVar

from django.db.models import Model, Q  # noqa: WPS347

from django_ninja_crudl.errors.mixin import ErrorHandlerMixin
from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.types import RequestDetails


class CrudlBaseMixin[TDjangoModel: Model](ErrorHandlerMixin):  # noqa: WPS214
    """Mixin for the CRUDL API."""

    _permission_classes: ClassVar[list[type[BasePermission]]] = []

    def has_permission(
        self,
        request: RequestDetails[TDjangoModel],
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
        request: RequestDetails[TDjangoModel],
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
        request: RequestDetails[TDjangoModel],
    ) -> bool:
        """Check if the user has permission to perform the action on the related object."""
        for permission_class in self._permission_classes:
            if not permission_class.__abstractmethods__:
                permission_instance = permission_class()
                if not permission_instance.has_related_object_permission(request):
                    return False
                return False
        return True

    def pre_create(self, request: RequestDetails[TDjangoModel]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Pre-create hook.

        Can be used to perform some actions or checks  before creating the object.
        """

    def post_create(
        self,
        request: RequestDetails[TDjangoModel],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Post-create hook.

        Can be used to perform some actions after creating the object.
        """

    def pre_update(self, request: RequestDetails[TDjangoModel]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Pre-update hook.

        Can be used to perform some actions or checks before updating the object.
        """

    def post_update(
        self,
        request: RequestDetails[TDjangoModel],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Post-update hook.

        Can be used to perform some actions after updating the object.
        """

    def pre_patch(
        self,
        request: RequestDetails[TDjangoModel],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Pre-patch hook.

        Can be used to perform some actions or checks before patching the object.
        """

    def post_patch(
        self,
        request: RequestDetails[TDjangoModel],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Post-patch hook.

        Can be used to perform some actions after patching the object.
        """

    def pre_delete(self, request: RequestDetails[TDjangoModel]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Pre-delete hook.

        Can be used to perform some actions or checks before deleting the object.
        """

    def post_delete(self, request: RequestDetails[TDjangoModel]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Post-delete hook.

        Can be used to perform some actions after deleting the object.
        """

    @abstractmethod
    def get_base_filter(
        self,
        request: RequestDetails[TDjangoModel],
    ) -> Q:
        """Return the base filter for all types of operations."""
        raise NotImplementedError

    @abstractmethod
    def get_filter_for_list(
        self,
        request: RequestDetails[TDjangoModel],
    ) -> Q:
        """Return the filter specific to the list operation."""
        raise NotImplementedError

    @abstractmethod
    def get_filter_for_update(
        self,
        request: RequestDetails[TDjangoModel],
    ) -> Q:
        """Return the filter specific to the update operation."""
        raise NotImplementedError

    @abstractmethod
    def get_filter_for_delete(
        self,
        request: RequestDetails[TDjangoModel],
    ) -> Q:
        """Return the filter specific to the delete operation."""
        raise NotImplementedError

    @abstractmethod
    def get_filter_for_get_one(
        self,
        request: RequestDetails[TDjangoModel],
    ) -> Q:
        """Return the filter specific to the get one operation."""
        raise NotImplementedError
