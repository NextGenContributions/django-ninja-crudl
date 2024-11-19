"""Super schema packages."""

from django_ninja_crudl.crudl import Crudl, CrudlApiBaseMeta
from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.types import (
    ObjectlessActions,
    PathArgs,
    RequestDetails,
    WithObjectActions,
)

__version__ = "0.0.0"

__all__ = [
    "Crudl",
    "CrudlApiBaseMeta",
    "ObjectlessActions",
    "WithObjectActions",
    "PathArgs",
    "RequestDetails",
    "BasePermission",
]
