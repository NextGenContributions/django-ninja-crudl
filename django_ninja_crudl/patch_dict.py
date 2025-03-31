"""Patch Schema with all fields set to optional."""

import functools
from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, cast

from ninja.utils import is_optional_type
from pydantic import BaseModel


def create_patch_schema(schema_cls: type[BaseModel]) -> type[BaseModel]:
    """Create a new schema class with all fields set to optional."""
    schema_cls_copy = deepcopy(schema_cls)
    for f in schema_cls_copy.__pydantic_fields__.values():
        t = f.annotation
        if t is not None and not is_optional_type(t):
            # Turn required fields into optional by assigning a default None value
            f.default = None

    # Define a custom 'model_dump' method that always exclude 'unset' values
    patched_model_dump = functools.partialmethod(
        schema_cls_copy.model_dump, exclude_unset=True
    )

    # The cloned schema should be recreated for the changes to take effect
    return cast(
        type[BaseModel],
        type(
            f"{schema_cls_copy.__name__}Patch",
            (schema_cls_copy,),
            {"model_dump": patched_model_dump},
        ),
    )


class PatchDictUtil:  # noqa: D101
    def __getitem__(self, schema_cls: type[BaseModel]) -> type[BaseModel]:
        """Replace the schema with a new one that has all fields set to optional."""
        return create_patch_schema(schema_cls)


if TYPE_CHECKING:  # pragma: nocover
    PatchDict = Annotated[dict, "<PatchDict>"]
else:
    PatchDict = PatchDictUtil()
