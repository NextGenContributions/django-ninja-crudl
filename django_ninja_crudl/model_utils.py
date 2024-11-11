"""Utility functions for working with Pydantic models."""

from typing import Optional, Union, get_args, get_origin

from pydantic import BaseModel


def extract_non_none_type(field_type: type) -> None | type:
    """Extract the actual type from Union[..., None] or Optional[...] types."""
    if get_origin(field_type) is Union or get_origin(field_type) is Optional:
        args = [arg for arg in get_args(field_type) if arg is not type(None)]
        return args[0] if args else None  # Return the first non-None type
    return field_type


def is_pydantic_model(model: type[BaseModel], field_name: str) -> bool:
    """Check if a field is a Pydantic model."""
    field_type = extract_non_none_type(model.__annotations__[field_name])
    return isinstance(field_type, type) and issubclass(field_type, BaseModel)


def is_list_of_pydantic_models(model: type[BaseModel], field_name: str) -> bool:
    """Check if a field is a list of Pydantic models."""
    field_type = extract_non_none_type(model.__annotations__[field_name])
    origin = get_origin(field_type)
    args = get_args(field_type)

    return (
        origin == list
        and args
        and isinstance(args[0], type)
        and issubclass(args[0], BaseModel)
    )


def get_pydantic_fields(
    model: type[BaseModel],
    field_name: str,
    prefix: str | None = None,
) -> list[str]:
    """Get the Pydantic fields of a model recursively.

    Returns:
        list[str]: A list of field names.

    Example return value:
        ["name", "age", "model_a__name", "model_a__age", "model_a__model_b__name", "model_a__model_b__age"]

    """
    if prefix:
        field_name = f"{prefix}__{field_name}"
    related_fields: list[str] = []
    field_type = model.__annotations__[field_name]
    print(f"field_name--->: {field_name}")
    if is_pydantic_model(model, field_name):
        field_type = extract_non_none_type(field_type)
        related_fields = [
            f"{field_name}__{related_field_name}"
            for related_field_name in field_type.__annotations__
        ]
    elif is_list_of_pydantic_models(model, field_name):
        field_type = extract_non_none_type(field_type)
        print(f"field_type: {field_type}")
        for related_field_name in field_type.__args__[0].__annotations__:
            print(f"related_field_name: {related_field_name}")
            related_fields.append(
                f"{field_name}__{related_field_name}",
            )
    print(f"related_fields: {related_fields}")
    return related_fields
