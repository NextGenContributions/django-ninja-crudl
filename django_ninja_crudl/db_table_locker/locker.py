"""Provide database-agnostic table locking utilities for Django."""

import logging
from typing import final

from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError, connection
from django.db.models import Model

from django_ninja_crudl.db_table_locker.exception import (
    TableLockError,
    TableUnlockError,
)
from django_ninja_crudl.db_table_locker.utils import get_table_name

logger = logging.getLogger(__name__)


@final
class DatabaseTableLocker:
    """Database-agnostic table locking utility for Django.

    Supports PostgreSQL, MySQL, SQLite, and Oracle with appropriate locking strategies
    for each database backend.
    """

    # Lock modes
    LOCK_SHARE = "SHARE"
    """Allows concurrent reads but prevents writes."""

    LOCK_EXCLUSIVE = "EXCLUSIVE"
    """Prevents all other access (reads and writes)."""

    def __init__(self, using: str = "default") -> None:
        """Initialize the DatabaseTableLocker class."""
        self.using = using
        self.connection = connection
        self.vendor = connection.vendor

    def _build_lock_statement(
        self, table_names: list[str], lock_mode: str
    ) -> str | None:
        """Build database-specific lock statement."""
        match self.vendor:
            case "postgresql":
                return self._postgresql_lock_statement(table_names, lock_mode)
            case "mysql":
                return self._mysql_lock_statement(table_names, lock_mode)
            case "sqlite":
                return self._sqlite_lock_statement(table_names, lock_mode)
            case "oracle":
                return self._oracle_lock_statement(table_names, lock_mode)
            case _:
                msg = f"Unsupported database vendor: {self.vendor}"
                raise ImproperlyConfigured(msg)

    def _postgresql_lock_statement(
        self, table_names: list[str], lock_mode: str
    ) -> str | None:
        """PostgreSQL LOCK TABLE statement."""
        # Map our generic lock modes to PostgreSQL lock statements
        pg_lock_modes = {
            self.LOCK_SHARE: "SHARE",
            self.LOCK_EXCLUSIVE: "EXCLUSIVE",
        }

        pg_mode = pg_lock_modes.get(lock_mode, "EXCLUSIVE")
        tables = ", ".join(f'"{name}"' for name in table_names)
        return f"LOCK TABLE {tables} IN {pg_mode} MODE"

    def _mysql_lock_statement(
        self, table_names: list[str], lock_mode: str
    ) -> str | None:
        """MySQL LOCK TABLES statement."""
        # MySQL uses different syntax - locks are acquired per table with READ/WRITE
        if lock_mode == self.LOCK_SHARE:
            locks = ", ".join(f"`{name}` READ" for name in table_names)
        else:
            locks = ", ".join(f"`{name}` WRITE" for name in table_names)
        return f"LOCK TABLES {locks}"

    def _sqlite_lock_statement(
        self, table_names: list[str], lock_mode: str
    ) -> str | None:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG002
        """SQLite doesn't support explicit table locking, but instead lock whole DB."""
        return None

    def _oracle_lock_statement(
        self, table_names: list[str], lock_mode: str
    ) -> str | None:
        """Oracle LOCK TABLE statement."""
        oracle_modes = {
            self.LOCK_SHARE: "SHARE",
            self.LOCK_EXCLUSIVE: "EXCLUSIVE",
        }

        oracle_mode = oracle_modes.get(lock_mode, "EXCLUSIVE")
        tables = ", ".join(name for name in table_names)
        return f"LOCK TABLE {tables} IN {oracle_mode} MODE"

    def _unlock_statement(self) -> str | None:
        """Build database-specific unlock statement."""
        if self.vendor == "mysql":
            return "UNLOCK TABLES"
        # PostgreSQL, Oracle, and SQLite release locks automatically on transaction end
        return None

    def lock_tables(
        self,
        tables: str | type[Model] | list[str | type[Model]],
        lock_mode: str = LOCK_EXCLUSIVE,
    ) -> None:
        """Lock one or more tables with specified lock mode.

        Args:
            tables: Single table/model or list of tables/models to lock
            lock_mode: Lock mode (SHARE, EXCLUSIVE)
        """
        if not isinstance(tables, list):
            tables = [tables]

        table_names = [get_table_name(table) for table in tables]
        if not (lock_sql := self._build_lock_statement(table_names, lock_mode)):
            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(lock_sql)
            msg = f"Locked tables {table_names} with mode {lock_mode}"
            logger.debug(msg)
        except DatabaseError as e:
            msg = f"Failed to lock tables {table_names}: {e}"
            raise TableLockError(msg) from e

    def unlock_tables(self) -> None:
        """Explicitly unlock tables if supported by the database."""
        if not (unlock_sql := self._unlock_statement()):
            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(unlock_sql)
            logger.debug("Explicitly unlocked tables")
        except DatabaseError as e:
            msg = f"Failed to explicitly unlock tables: {e}"
            raise TableUnlockError(msg) from e
