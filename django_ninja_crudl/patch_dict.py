from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, Any

from ninja import Body
from ninja.utils import is_optional_type
from pydantic_core import core_schema


class ModelToDict(dict):
    _wrapped_model: Any = None
    _wrapped_model_dump_params: dict[str, Any] = {}

    @classmethod
    def __get_pydantic_core_schema__(cls, _source: Any, _handler: Any) -> Any:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            cls._wrapped_model.__pydantic_core_schema__,
        )

    @classmethod
    def _validate(cls, input_value: Any) -> Any:
        return input_value.model_dump(**cls._wrapped_model_dump_params)


def create_patch_schema(schema_cls: type[Any]) -> type[ModelToDict]:
    # Turn required fields into optional by assigning a default None value
    schema_cls_copy = deepcopy(schema_cls)
    for f in schema_cls_copy.__pydantic_fields__.values():
        t = f.annotation
        if not is_optional_type(t):
            f.default = None
    # The cloned schema should be recreated for the changes to take effect
    OptionalSchema = type(f"{schema_cls.__name__}Patch", (schema_cls,), {})

    class OptionalDictSchema(ModelToDict):
        _wrapped_model = OptionalSchema
        _wrapped_model_dump_params = {"exclude_unset": True}

    return OptionalDictSchema


class PatchDictUtil:
    def __getitem__(self, schema_cls: Any) -> Any:
        new_cls = create_patch_schema(schema_cls)
        return Body[new_cls]  # type: ignore


if TYPE_CHECKING:  # pragma: nocover
    PatchDict = Annotated[dict, "<PatchDict>"]
else:
    PatchDict = PatchDictUtil()
