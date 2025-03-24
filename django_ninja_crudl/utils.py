"""Utility functions for the django_ninja_crudl package."""

import inspect
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar, final, override

from beartype import beartype
from django.db import models
from django.db.models import Model
from django2pydantic import BaseSchema
from django2pydantic.schema import SchemaConfig
from ninja import Path
from pydantic import BaseModel

from django_ninja_crudl.types import TDjangoModel_co


def get_path_spec_args(path_spec: str) -> list[str]:
    """Extract list of arguments from path spec.

    Args:
        path_spec: The path specification (e.g., "/publishers/{id}")

    Returns:
        List of argument names
    """
    path_args = []
    for part in path_spec.split("/"):
        if part.startswith("{") and part.endswith("}"):
            # Extract just the argument name without type annotation
            arg_name = part[1:-1]
            if ":" in arg_name:
                _, arg_name = arg_name.split(":", 1)
            path_args.append(arg_name)

    return path_args


def get_pydantic_model_from_args_annotations(
    model_class: type[TDjangoModel_co], path_args: list[str]
) -> type[BaseModel]:
    """Create a Pydantic model to validate path arguments."""
    if not path_args:
        # Return a dummy model with a dummy field to avoid django-ninja treating
        # 'path_args' as a path parameter
        class DummyPathArgsSchema(BaseModel):
            obfuscated_dummy_field_2EbghJ4DDXgAxxnPUsk34u8uAk83tj: str | None = None

            @override
            def model_dump(self, **kwargs) -> dict[str, Any]:
                """Force the dump to always return nothing."""
                return {}

        return DummyPathArgsSchema

    @final
    class PathArgsSchema(BaseSchema[models.Model]):  # pylint: disable=too-few-public-methods
        config = SchemaConfig[models.Model](
            model=model_class,
            fields=path_args,
            name=f"{model_class.__name__}PathArgs",
        )

    return PathArgsSchema


def replace_path_args_annotation(
    path_spec: str, model_class: type[TDjangoModel_co]
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Replace 'path_args' in signature with a properly annotated Pydantic model."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        new_signature = inspect.signature(func)

        # Exclude placeholder 'path_args' from function's params if it exists
        new_params = list(new_signature.parameters.values())
        new_params = [param for param in new_params if param.name != "path_args"]

        # Add the new properly annotated 'path_args' to the list of parameters
        path_spec_args = get_path_spec_args(path_spec)
        if path_spec_args:
            new_path_args_param: type[BaseSchema[models.Model]] = (
                get_pydantic_model_from_args_annotations(model_class, path_spec_args)
            )
            new_params.insert(
                len(new_params) - 2,
                inspect.Parameter(
                    "path_args",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=Path[new_path_args_param],
                ),
            )

        new_signature = new_signature.replace(parameters=new_params)
        wrapper.__signature__ = new_signature
        return wrapper

    return decorator


T = TypeVar("T", bound=Model)
SaveMethod = Callable[..., None]


@beartype
@contextmanager
def validating_manager(model_class: type[T]) -> Generator[None, None, None]:
    """Replace the save method of a model class with a version that calls full_clean() before save."""
    original_save: SaveMethod = model_class.save

    def validating_save(self: T, *args: Any, **kwargs: Any) -> None:
        """Call full_clean() before saving."""
        if not self.pk:
            self.full_clean()
        return original_save(self, *args, **kwargs)

    model_class.save = validating_save
    try:
        yield
    finally:
        model_class.save = original_save
