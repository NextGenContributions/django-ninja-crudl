"""Context manager for database table locking."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.db.models import Model

from django_ninja_crudl.db_table_locker.locker import DatabaseTableLocker


@contextmanager
def lock_tables(
    tables: str | type[Model] | list[str | type[Model]],
    lock_mode: str = DatabaseTableLocker.LOCK_EXCLUSIVE,
) -> Generator[None, Any, None]:  # pyright: ignore[reportExplicitAny]
    """Context manager for database-agnostic table locking.

    Usage:
        # Lock single table
        with lock_tables(MyModel):
            # Do work with locked table
            pass

        # Lock multiple tables
        with lock_tables([MyModel, AnotherModel], lock_mode='SHARE'):
            # Do work with locked tables
            pass

        # Lock by table name
        with lock_tables('my_table_name'):
            # Do work
            pass

    Args:
        tables: Single table/model or list of tables/models to lock
        lock_mode: Lock mode ('SHARE', 'EXCLUSIVE')
    """
    # Ensure we're in a transaction
    if not connection.in_atomic_block:
        msg = (
            "Table locking must be used within a database transaction. "
            "Use @transaction.atomic or with transaction.atomic():"
        )
        raise ImproperlyConfigured(msg)

    locker = DatabaseTableLocker(using=connection.alias)

    try:
        # Acquire locks
        locker.lock_tables(tables, lock_mode)
        yield
    finally:
        # Explicitly unlock for databases that support it
        locker.unlock_tables()
        # Transaction end will release locks automatically


@contextmanager
def atomic_lock_tables(
    tables: str | type[Model] | list[str | type[Model]],
    lock_mode: str = DatabaseTableLocker.LOCK_EXCLUSIVE,
    using: str = "default",
) -> Generator[None, Any, None]:  # pyright: ignore[reportExplicitAny]
    """Combination of atomic transaction and table locking.

    This is a convenience method that wraps both transaction.atomic()
    and table locking in a single context manager.

    Usage:
        with atomic_table_lock(MyModel):
            # Work is done in a transaction with table locked
            MyModel.objects.create(name='test')
    """
    with (
        transaction.atomic(using=using),
        lock_tables(tables, lock_mode),
    ):
        yield
