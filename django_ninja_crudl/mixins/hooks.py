"""Mixins for pre and post hooks."""

from abc import ABC
from typing import Generic

from django_ninja_crudl.types import RequestDetails, TDjangoModel_co


class HooksMixin(Generic[TDjangoModel_co], ABC):
    """Mixin for pre and post hooks."""

    def pre_create(self, request: RequestDetails[TDjangoModel_co]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Pre-create hook.

        Can be used to perform some actions or checks before creating the object.
        """

    def post_create(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Post-create hook.

        Can be used to perform some actions after creating the object.
        """

    def pre_update(self, request: RequestDetails[TDjangoModel_co]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Pre-update hook.

        Can be used to perform some actions or checks before updating the object.
        """

    def post_update(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Post-update hook.

        Can be used to perform some actions after updating the object.
        """

    def pre_patch(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Pre-patch hook.

        Can be used to perform some actions or checks before patching the object.
        """

    def post_patch(
        self,
        request: RequestDetails[TDjangoModel_co],  # pyright: ignore[reportUnusedParameter]
    ) -> None:
        """Post-patch hook.

        Can be used to perform some actions after patching the object.
        """

    def pre_delete(self, request: RequestDetails[TDjangoModel_co]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Pre-delete hook.

        Can be used to perform some actions or checks before deleting the object.
        """

    def post_delete(self, request: RequestDetails[TDjangoModel_co]) -> None:  # pyright: ignore[reportUnusedParameter]
        """Post-delete hook.

        Can be used to perform some actions after deleting the object.
        """
