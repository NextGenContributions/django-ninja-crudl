"""Permissions for CRUDL views."""

from enum import Enum


class ActionTypes(Enum):
    """Action types for permissions."""

    CREATE = "create"
    READ = "read"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
