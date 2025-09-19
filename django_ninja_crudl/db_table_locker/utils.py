"""Utility functions."""

from django.db.models import Model


def get_table_name(model_or_table: str | type[Model]) -> str:
    """Get the actual database table name from model or string."""
    if isinstance(model_or_table, str):
        return model_or_table

    if hasattr(model_or_table, "_meta"):
        return model_or_table._meta.db_table  # noqa: SLF001

    msg = "Expected model class or table name string"
    raise ValueError(msg)
