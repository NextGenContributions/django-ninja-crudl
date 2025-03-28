"""Endpoints for CRUDL operations in Django Ninja CRUDL."""

from .create import get_create_endpoint
from .delete import get_delete_endpoint
from .get_one import get_get_one_endpoint
from .list import get_get_many_endpoint
from .partial_update import get_partial_update_endpoint
from .update import get_update_endpoint

__all__ = [
    "get_create_endpoint",
    "get_delete_endpoint",
    "get_get_many_endpoint",
    "get_get_one_endpoint",
    "get_partial_update_endpoint",
    "get_update_endpoint",
]
