"""Decorators for convenience."""

from collections.abc import Callable
from typing import Any

from django.db.models import Model

from django_ninja_crudl.db_table_locker.context_manager import (
    atomic_lock_tables,
    lock_tables,
)
from django_ninja_crudl.db_table_locker.locker import DatabaseTableLocker


def require_lock_tables(
    tables: str | type[Model] | list[str | type[Model]],
    lock_mode: str = DatabaseTableLocker.LOCK_EXCLUSIVE,
) -> Callable[[Any], Callable[[tuple[Any, ...], dict[str, Any]], Any]]:  # pyright: ignore[reportExplicitAny]
    """Decorator that ensures a function runs with specified tables locked.

    Usage:
        @require_table_lock(MyModel)
        @transaction.atomic
        def my_function():
            # Function runs with MyModel table locked
            pass
    """

    def decorator(func: Callable) -> Callable:  # type: ignore[type-arg]
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def] # noqa: ANN002, ANN003, ANN202
            with lock_tables(tables, lock_mode):
                return func(*args, **kwargs)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]

        return wrapper  # pyright: ignore[reportUnknownVariableType]

    return decorator  # pyright: ignore[reportUnknownVariableType]


def require_atomic_lock_tables(
    tables: str | type[Model] | list[str | type[Model]],
    lock_mode: str = DatabaseTableLocker.LOCK_EXCLUSIVE,
    using: str = "default",
) -> Callable[[Any], Callable[[tuple[Any, ...], dict[str, Any]], Any]]:  # pyright: ignore[reportExplicitAny]
    """Decorator that wraps function in atomic transaction with table locking.

    Usage:
        @require_atomic_table_lock([MyModel, AnotherModel])
        def my_function():
            # Function runs atomically with tables locked
            pass
    """

    def decorator(func: Callable) -> Callable:  # type: ignore[type-arg]
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def] # noqa: ANN002, ANN003, ANN202
            with atomic_lock_tables(tables, lock_mode, using):
                return func(*args, **kwargs)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]

        return wrapper  # pyright: ignore[reportUnknownVariableType]

    return decorator  # pyright: ignore[reportUnknownVariableType]
