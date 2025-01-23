"""Base class for the CrudlController which provides the needed feature methods."""

from abc import ABC
from typing import Generic

from beartype import beartype

from django_ninja_crudl.errors.mixin import ErrorHandlerMixin
from django_ninja_crudl.mixins.filters import FiltersMixin
from django_ninja_crudl.mixins.hooks import HooksMixin
from django_ninja_crudl.mixins.permissions import PermissionMixin
from django_ninja_crudl.mixins.utilities import UtilitiesMixin
from django_ninja_crudl.types import TDjangoModel_co


@beartype
class CrudlBaseMethodsMixin(  # noqa: WPS215 too many base classes
    Generic[TDjangoModel_co],
    ErrorHandlerMixin,
    FiltersMixin[TDjangoModel_co],
    HooksMixin[TDjangoModel_co],
    PermissionMixin[TDjangoModel_co],
    UtilitiesMixin[TDjangoModel_co],
    ABC,
):
    """Provide base feature methods for the CrudlController."""
