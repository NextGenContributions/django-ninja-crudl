"""Mixins for pre- and post-hooks."""

# pyright: reportUnusedParameter=false

from abc import ABC
from typing import Generic

from django_ninja_crudl.types import RequestDetails, TDjangoModel


class HooksMixin(Generic[TDjangoModel], ABC):
    """Mixin for pre- and post-hooks."""

    def pre_create(self, request: RequestDetails[TDjangoModel]) -> None:
        """Pre-create hook.

        Can be used to perform some actions or checks before creating the object.
        """

    def post_create(self, request: RequestDetails[TDjangoModel]) -> None:
        """Post-create hook.

        Can be used to perform some actions after creating the object.
        """

    def pre_update(self, request: RequestDetails[TDjangoModel]) -> None:
        """Pre-update hook.

        Can be used to perform some actions or checks before updating the object.
        """

    def post_update(self, request: RequestDetails[TDjangoModel]) -> None:
        """Post-update hook.

        Can be used to perform some actions after updating the object.
        """

    def pre_patch(self, request: RequestDetails[TDjangoModel]) -> None:
        """Pre-patch hook.

        Can be used to perform some actions or checks before patching the object.
        """

    def post_patch(self, request: RequestDetails[TDjangoModel]) -> None:
        """Post-patch hook.

        Can be used to perform some actions after patching the object.
        """

    def pre_delete(self, request: RequestDetails[TDjangoModel]) -> None:
        """Pre-delete hook.

        Can be used to perform some actions or checks before deleting the object.
        """

    def post_delete(self, request: RequestDetails[TDjangoModel]) -> None:
        """Post-delete hook.

        Can be used to perform some actions after deleting the object.
        """
