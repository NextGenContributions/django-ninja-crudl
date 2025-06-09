"""Utility functions for the django_ninja_crudl package."""

import inspect
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, final

from beartype import beartype
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Field, ForeignObjectRel
from django.http import HttpRequest
from django2pydantic import BaseSchema
from django2pydantic.schema import SchemaConfig
from ninja import Path

from django_ninja_crudl.types import TDjangoModel


def get_model_field(
    model_class: type[TDjangoModel], field_name: str
) -> Field[Any, Any] | ForeignObjectRel | GenericForeignKey:
    """Get the field object from Django's model class.

    Exceptions:
        - FieldDoesNotExist: If the field does not exist in the model.
    """
    return model_class._meta.get_field(field_name)  # noqa: SLF001  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType]


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
    model_class: type[TDjangoModel], path_args: list[str]
) -> type[BaseSchema[TDjangoModel]]:
    """Create a Pydantic model to validate path arguments."""

    @final
    class PathArgsSchema(BaseSchema[TDjangoModel]):  # pyright: ignore [reportGeneralTypeIssues,reportUninitializedInstanceVariable]
        config: SchemaConfig[TDjangoModel] = SchemaConfig[TDjangoModel](
            model=model_class,
            fields=path_args,
            name=f"{model_class.__name__}PathArgs",
        )

    return PathArgsSchema


def replace_path_args_annotation(
    path_spec: str, model_class: type[TDjangoModel]
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
            new_path_args_param = get_pydantic_model_from_args_annotations(
                model_class, path_spec_args
            )
            new_params.insert(
                len(new_params) - 2,  # Insert before the last parameter (kwargs)
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


SaveMethod = Callable[..., None]


@beartype
@contextmanager
def validating_manager(model_class: type[TDjangoModel]) -> Generator[None, None, None]:
    """Replace the save method of a model class with a version that calls full_clean() before save."""
    original_save: SaveMethod = model_class.save

    def validating_save(self: TDjangoModel, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401  # pyright: ignore [reportExplicitAny, reportAny]
        """Call full_clean() before saving."""
        self.full_clean()
        return original_save(self, *args, **kwargs)

    model_class.save = validating_save  # type: ignore[method-assign,assignment]
    try:
        yield
    finally:
        model_class.save = original_save  # type: ignore[method-assign]


def get_request_id(request: HttpRequest) -> str:
    """Return the request ID from the request headers."""
    return request.headers.get("X-Request-ID", "")
