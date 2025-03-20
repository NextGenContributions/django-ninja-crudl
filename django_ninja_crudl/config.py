"""Configuration classes for the CRUDL controller."""

from dataclasses import dataclass
from typing import Generic, final, overload, override

from beartype import beartype
from django.db import models
from django2pydantic import BaseSchema
from django2pydantic.schema import SchemaConfig
from ninja import PatchDict
from pydantic import BaseModel

from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.schema import Schema
from django_ninja_crudl.types import TDjangoModel, TDjangoModel_co


@dataclass(kw_only=True)
class CrudlConfig(Generic[TDjangoModel_co]):  # pylint: disable=too-many-instance-attributes # noqa: WPS230
    """Configuration for the CrudlController."""

    '''
    model: type[TDjangoModel_co]
    """The Django model to be used."""

    base_path: str | None
    """The base path for the CRUDL operations.

    If not provided, it will be generated from the model name.
    """

    create_schema: type[BaseModel] | None
    """The request schema for the create endpoint.

    If not provided, the endpoint will not be created.
    """

    update_schema: type[BaseModel] | None
    """The request schema for the update endpoint.

    If not provided, the endpoint will not be created.
    """

    partial_update_schema: type[BaseModel] | None
    """The request schema for the partial update endpoint.

    If not provided, the endpoint will not be created.
    """

    get_one_schema: type[BaseModel] | None
    """The request schema for the get one endpoint.

    If not provided, the endpoint will not be created.
    """

    list_schema: type[BaseModel] | None
    """The request schema for the list endpoint.

    If not provided, the endpoint will not be created.
    """

    delete_allowed: bool
    """Whether the delete endpoint is created."""

    create_response_name: str | None
    """The name of the response class for the create operation."""

    create_response_schema: type[BaseModel] | None
    """The schema for the create response."""

    create_path: str
    """The path for the create endpoint."""

    update_path: str
    """The path for the update endpoint."""

    get_one_path: str
    """The path for the get one endpoint."""

    list_path: str
    """The path for the list endpoint."""

    delete_path: str
    """The path for the delete endpoint."""

    path_schema: type[BaseModel] | None

    create_operation_id: str
    """The operation ID for the create endpoint."""

    update_operation_id: str
    """The operation ID for the update endpoint."""

    partial_update_operation_id: str
    """The operation ID for the partial update endpoint."""

    get_one_operation_id: str
    """The operation ID for the get one endpoint."""

    list_operation_id: str
    """The operation ID for the list endpoint."""

    delete_operation_id: str
    """The operation ID for the delete endpoint."""

    permission_classes: list[type[BasePermission]] | None
    '''

    @override
    def __init__(  # noqa: WPS211 pylint: disable=too-many-arguments, too-many-locals,too-many-positional-arguments
        self,
        model: type[TDjangoModel_co],
        base_path: str | None = None,
        create_schema: Schema[TDjangoModel_co] | type[BaseModel] | None = None,
        update_schema: Schema[TDjangoModel_co] | type[BaseModel] | None = None,
        get_one_schema: Schema[TDjangoModel_co] | type[BaseModel] | None = None,
        list_schema: Schema[TDjangoModel_co] | type[BaseModel] | None = None,
        delete_allowed: bool = False,
        create_path: str | None = None,
        update_path: str | None = None,
        get_one_path: str | None = None,
        list_path: str | None = None,
        delete_path: str | None = None,
        create_operation_id: str | None = None,
        update_operation_id: str | None = None,
        partial_update_operation_id: str | None = None,
        get_one_operation_id: str | None = None,
        delete_operation_id: str | None = None,
        list_operation_id: str | None = None,
        permission_classes: list[type[BasePermission]] | None = None,
    ) -> None:
        """Initialize the CrudlConfig class."""
        if not base_path:
            model_plural_name = self.model.__name__.lower().replace(" ", "-")
            self.base_path = f"/{model_plural_name}"
        else:
            self.base_path = base_path
        self.model = model

        self.create_schema = self._set_schema(create_schema, model)
        self.update_schema = self._set_schema(update_schema, model)
        if self.update_schema:
            self.partial_update_schema = PatchDict[self.update_schema]
        else:
            self.partial_update_schema = None

        self.get_one_schema = self._set_schema(get_one_schema, model)
        self.list_schema = self._set_schema(list_schema, model)

        self.delete_allowed = delete_allowed

        self.create_response_schema = self._get_create_response_schema(model)
        self.create_response_name = self.create_response_schema.__name__

        pk_name = self._get_pk_name(model)
        pk_type = self._get_pk_type(model)

        # Set or generate the paths
        id_string = f"{{{pk_type}:{pk_name}}}"
        self.create_path = create_path or f"{base_path}"
        self.get_one_path = get_one_path or f"{base_path}/{id_string}"
        self.update_path = update_path or f"{base_path}/{id_string}"
        self.delete_path = delete_path or f"{base_path}/{id_string}"
        self.list_path = list_path or f"{base_path}"

        # Set or generate the OpenAPI operation IDs
        self.create_operation_id = create_operation_id or f"{model.__name__}_create"
        self.update_operation_id = update_operation_id or f"{model.__name__}_update"
        self.partial_update_operation_id = (
            partial_update_operation_id or f"{model.__name__}_partial_update"
        )
        self.get_one_operation_id = get_one_operation_id or f"{model.__name__}_get_one"
        self.list_operation_id = list_operation_id or f"{model.__name__}_list"
        self.delete_operation_id = delete_operation_id or f"{model.__name__}_delete"

        self.path_schema = self._get_path_schema(model)

        self.tags = [model.__name__]

        if permission_classes:
            self.permission_classes = permission_classes

        super().__init__()

    @classmethod
    def _get_path_schema(cls, model_class: type[models.Model]) -> type[BaseModel]:
        """Get the path class."""

        @final
        class PathId(BaseSchema[models.Model]):
            """Path ID class."""

            config = SchemaConfig[models.Model](
                model=model_class,
                fields=[cls._get_pk_name(model_class)],
            )

        return PathId

    @overload
    @staticmethod
    def _set_schema(schema_def: None, model: type[TDjangoModel]) -> None: ...

    @overload
    @staticmethod
    def _set_schema(
        schema_def: type[BaseModel] | Schema[TDjangoModel], model: type[TDjangoModel]
    ) -> type[BaseModel]: ...

    @staticmethod
    def _set_schema(
        schema_def: type[BaseModel] | Schema[TDjangoModel] | None,
        model: type[TDjangoModel],
    ) -> type[BaseModel] | None:
        """Return the endpoint schema."""
        if schema_def is None:
            return None
        if isinstance(schema_def, Schema):
            return schema_def.create_pydantic_model(model)
        if schema_def is BaseModel:
            return schema_def

        pydantic_model_module = f"{BaseModel.__module__}.{BaseModel.__qualname__}"
        schema_module = f"{Schema.__module__}.{Schema.__qualname__}"
        msg = (
            f"Invalid create schema: {schema_def}. "
            f"It must be an instance or subclass of {schema_module} or "
            f"{pydantic_model_module}."
        )
        raise ValueError(msg)

    @beartype
    @staticmethod
    def _get_pk_name(model_class: type[models.Model]) -> str:
        pk = model_class._meta.pk  # noqa: SLF001
        if pk is None:
            msg = f"Model {model_class.__name__} doesn't have a primary key"
            raise ValueError(msg)
        return pk.name

    @beartype
    @staticmethod
    def _get_pk_type(model_class: type[models.Model]) -> str:
        """Get the primary key type."""
        field = model_class._meta.pk  # noqa: SLF001, WPS437

        if isinstance(field, models.IntegerField):
            return "int"
        if isinstance(field, models.UUIDField):
            return "uuid"
        msg = f"Unknown primary key type: {field}"
        raise TypeError(msg)

    @classmethod
    def _get_create_response_schema(
        cls, model_class: type[models.Model]
    ) -> type[BaseModel]:
        """Get the create response schema."""

        @final
        class CreateResponseSchema(BaseSchema[models.Model]):
            """Create response schema."""

            config = SchemaConfig[models.Model](
                model=model_class,
                fields=["id"],
                name=f"Create{model_class.__name__}Response",
            )

        return CreateResponseSchema
