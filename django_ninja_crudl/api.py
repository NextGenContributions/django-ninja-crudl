"""Django Ninja CRUDL API."""

from typing import override

from ninja.openapi.schema import OpenAPISchema
from ninja.params.models import TModel
from ninja.types import DictStrAny
from ninja_extra import NinjaExtraAPI


class NinjaCrudlOpenAPISchema(OpenAPISchema):
    """OpenAPI schema for the CRUDL API."""

    @override
    def _extract_parameters(self, model: TModel) -> list[DictStrAny]:  # pyright: ignore [reportInvalidTypeVarUse]
        """Extract parameters from the model."""
        result = super()._extract_parameters(model)
        # Remove "examples" from the parameters as they are just copies of "examples"
        # in the pydantic schemas, which is a list of values and not a dict. This is
        # problematic because Parameters' "examples" is supposed to be a dict.
        # Assigning a list to it would cause issue with API docs and schemathesis tests.
        for param in result:
            _ = param.pop("examples", None)  # pyright: ignore [reportAny]
        return result


class NinjaCrudlAPI(NinjaExtraAPI):
    """Ninja Extra API with CRUDL support."""

    @override
    def get_openapi_schema(
        self,
        *,
        path_prefix: str | None = None,
        path_params: DictStrAny | None = None,
    ) -> OpenAPISchema:
        """Get the OpenAPI schema for the API."""
        if path_prefix is None:
            path_prefix = self.get_root_path(path_params or {})
        return NinjaCrudlOpenAPISchema(self, path_prefix)
