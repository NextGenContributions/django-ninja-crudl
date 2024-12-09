"""Super schema packages."""

from django2pydantic import Infer, ModelFields  # hoisting/bubble up
from django_ninja_crudl.crudl import Crudl, CrudlApiBaseMeta
from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.types import (
    ObjectlessActions,
    PathArgs,
    RequestDetails,
    WithObjectActions,
)

__version__ = "0.2.1"

__all__ = [
    "Crudl",
    "CrudlApiBaseMeta",
    "ObjectlessActions",
    "WithObjectActions",
    "PathArgs",
    "RequestDetails",
    "BasePermission",
    "ModelFields",
    "Infer",
]
