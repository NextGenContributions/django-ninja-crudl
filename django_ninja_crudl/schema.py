"""Shared types for the CRUDL classes."""

from typing import Generic, final

from django2pydantic import BaseSchema, ModelFields
from django2pydantic.schema import SchemaConfig
from django_ninja_crudl.types import TDjangoModel, TDjangoModel_co


class Schema(Generic[TDjangoModel_co]):
    """Deferred Schema for the CRUDL classes."""

    def __init__(self, fields: ModelFields) -> None:
        """Initialize the Schema class."""
        self.fields: ModelFields = fields
        super().__init__()

    def create_pydantic_model(
        self, model: type[TDjangoModel]
    ) -> type[BaseSchema[TDjangoModel_co]]:
        """Create a Pydantic model from the schema."""
        meta_name = f"{model.__name__}Schema"
        meta_fields = self.fields
        meta_model = model

        @final
        class MyModel(BaseSchema):  # noqa: WPS431
            """Pydantic model for the schema."""

            config = SchemaConfig(
                model=meta_model,
                fields=meta_fields,
                name=meta_name,
            )

        return MyModel
