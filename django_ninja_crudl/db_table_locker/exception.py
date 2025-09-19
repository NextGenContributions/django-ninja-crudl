"""Exceptions for DB table locking."""

from django.db import DatabaseError


class TableLockError(DatabaseError):
    """Raised when table locking operations fail."""


class TableUnlockError(DatabaseError):
    """Raised when table unlocking operations fail."""
