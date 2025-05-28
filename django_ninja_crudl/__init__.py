"""Super schema packages."""

from django2pydantic import Infer, ModelFields  # hoisting/bubbling up
from ninja_extra import ControllerBase, status  # hoisting/bubbling up

from django_ninja_crudl.config import CrudlConfig
from django_ninja_crudl.crudl_controller import CrudlController
from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.schema import Schema
from django_ninja_crudl.types import (
    ObjectlessActions,
    PathArgs,
    RequestDetails,
    WithObjectActions,
)

__version__ = "0.5.3"

__all__ = [
    "BasePermission",
    "ControllerBase",
    "CrudlConfig",
    "CrudlController",
    "Infer",
    "ModelFields",
    "ObjectlessActions",
    "PathArgs",
    "RequestDetails",
    "Schema",
    "WithObjectActions",
    "status",
]
