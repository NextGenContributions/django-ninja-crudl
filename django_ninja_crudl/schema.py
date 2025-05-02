"""Shared types for the CRUDL classes."""

from typing import Generic, final

from django2pydantic import BaseSchema, ModelFields, ModelFieldsCompact
from django2pydantic.schema import SchemaConfig

from django_ninja_crudl.types import TDjangoModel


class Schema(Generic[TDjangoModel]):
    """Deferred Schema for the CRUDL classes."""

    def __init__(self, fields: ModelFields | ModelFieldsCompact) -> None:
        """Initialize the Schema class."""
        self.fields: ModelFields | ModelFieldsCompact = fields
        super().__init__()

    def create_pydantic_model(
        self,
        model: type[TDjangoModel],  # pyright: ignore [reportGeneralTypeIssues]
        suffix: str = "",
    ) -> type[BaseSchema[TDjangoModel]]:
        """Create a Pydantic model from the schema."""
        meta_name = f"{model.__name__}Schema{suffix}"
        meta_fields = self.fields
        meta_model = model

        @final
        class MyModel(BaseSchema[TDjangoModel]):  # noqa: WPS431  # pyright: ignore [reportGeneralTypeIssues, reportUninitializedInstanceVariable]
            """Pydantic model for the schema."""

            config: SchemaConfig[TDjangoModel] = SchemaConfig[TDjangoModel](  # pyright: ignore [reportGeneralTypeIssues]
                model=meta_model,
                fields=meta_fields,
                name=meta_name,
            )

        return MyModel
