"""Utility functions for the django_ninja_crudl package."""

import inspect
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar
from uuid import UUID

from django.db.models import Model


def extract_arguments_from_path_spec(path_spec: str) -> dict[str, type]:
    """Extract arguments from the path spec.

    Args:
        path_spec (str): The path spec. For example: "/{uuid:organization}/resource/{uuid:id}"

    Returns:
        dict[str, type]: A dictionary with the argument names as keys and the argument types as values. For example: {"organization": UUID, "id": UUID}.

    """
    args_with_types: dict[str, type] = {}
    for part in path_spec.split("/"):
        if part.startswith("{") and part.endswith("}"):
            arg_type, arg_name = part[1:-1].split(":")
            if arg_type == "uuid":
                arg_type = UUID
            elif arg_type == "int":
                arg_type = int
            elif arg_type == "str":
                arg_type = str
            args_with_types[arg_name] = arg_type
    return args_with_types


def add_function_arguments(path_spec: str) -> Callable[[Callable], Callable]:
    """Add function arguments to the decorated function."""
    new_args_with_types: dict[str, type] = extract_arguments_from_path_spec(path_spec)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **path_args):
            return func(*args, **path_args)

        new_signature = inspect.signature(func)

        # add the new arguments to the signature before the **kwargs:
        new_params = list(new_signature.parameters.values())
        new_params = (
            new_params[:-1]
            + [
                inspect.Parameter(
                    name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=new_args_with_types[name],
                )
                for name in new_args_with_types
            ]
            + new_params[-1:]
        )
        new_signature = new_signature.replace(parameters=new_params)

        wrapper.__signature__ = new_signature
        return wrapper

    return decorator


T = TypeVar("T", bound=Model)
SaveMethod = Callable[..., None]


@contextmanager
def validating_manager(model_class: type[T]) -> Generator[None, None, None]:
    """Replace the save method of a model class with a version that calls full_clean() before save."""
    original_save: SaveMethod = model_class.save

    def validating_save(self: T, *args: Any, **kwargs: Any) -> None:
        """Call full_clean() before saving."""
        print(self)
        if not self.pk:
            self.full_clean()
        return original_save(self, *args, **kwargs)

    model_class.save = validating_save
    try:
        yield
    finally:
        model_class.save = original_save
