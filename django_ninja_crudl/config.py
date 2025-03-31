"""Configuration classes for the CRUDL controller."""

from dataclasses import dataclass
from typing import Generic, final, overload, override

from beartype import beartype
from django2pydantic import BaseSchema
from django2pydantic.schema import SchemaConfig
from pydantic import BaseModel

from django_ninja_crudl.patch_dict import PatchDict
from django_ninja_crudl.permissions import BasePermission
from django_ninja_crudl.schema import Schema
from django_ninja_crudl.types import TDjangoModel


@dataclass(kw_only=True)
class CrudlConfig(Generic[TDjangoModel]):  # pylint: disable=too-many-instance-attributes
    """Configuration for the CrudlController.

    model: type[TDjangoModel]: The Django model to be used.

    base_path: str | None: The base path for the CRUDL operations. If not provided,
        it will be generated from the model name.

    create_schema: type[BaseModel] | None: The request schema for the create endpoint.
        If not provided, the endpoint will not be created.

    update_schema: type[BaseModel] | None: The request schema for the update endpoint.
        If not provided, the endpoint will not be created.

    partial_update_schema: type[BaseModel] | None: The request schema for the
        partial update endpoint. If not provided, the endpoint will not be created.

    get_one_schema: type[BaseModel] | None: The request schema for the get one endpoint.
        If not provided, the endpoint will not be created.

    list_schema: type[BaseModel] | None: The request schema for the list endpoint.
        If not provided, the endpoint will not be created.

    delete_allowed: bool: Whether the delete endpoint is created.

    create_response_name: str | None: The name of the response class for the
        create operation.

    create_response_schema: type[BaseModel] | None: The schema for the create response.

    create_path: str: The path for the create endpoint.

    update_path: str: The path for the update endpoint.

    get_one_path: str: The path for the get one endpoint.

    list_path: str: The path for the list endpoint.

    delete_path: str: The path for the delete endpoint.

    path_schema: type[BaseModel] | None

    create_operation_id: str: The operation ID for the create endpoint.

    update_operation_id: str: The operation ID for the update endpoint.

    partial_update_operation_id: str: The operation ID for the partial update endpoint.

    get_one_operation_id: str: The operation ID for the get one endpoint.

    list_operation_id: str: The operation ID for the list endpoint.

    delete_operation_id: str: The operation ID for the delete endpoint.

    permission_classes: list[type[BasePermission]] | None
    """

    @override
    def __init__(  # noqa: WPS211, WPS231  # pylint: disable=too-many-arguments, too-many-locals,too-many-positional-arguments
        self,
        model: type[TDjangoModel],
        base_path: str | None = None,
        create_schema: Schema[TDjangoModel] | type[BaseModel] | None = None,
        update_schema: Schema[TDjangoModel] | type[BaseModel] | None = None,
        get_one_schema: Schema[TDjangoModel] | type[BaseModel] | None = None,
        list_schema: Schema[TDjangoModel] | type[BaseModel] | None = None,
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
        permission_classes: list[type[BasePermission[TDjangoModel]]] | None = None,
    ) -> None:
        """Initialize the CrudlConfig class."""
        self.base_path: str
        if base_path:
            self.base_path = base_path
        else:
            model_plural_name = model.__name__.lower().replace(" ", "-")
            self.base_path = f"/{model_plural_name}"
        self.model: type[TDjangoModel] = model

        # Set or generate the schemas for CRUDL operations
        self.get_one_schema: type[BaseModel] | None
        self.list_schema: type[BaseModel] | None
        self.create_schema: type[BaseModel] | None
        self.create_response_schema: type[BaseModel] | None
        self.update_schema: type[BaseModel] | None
        self.partial_update_schema: type[BaseModel] | None

        self.delete_allowed: bool = delete_allowed
        self.get_one_schema = self._set_schema(get_one_schema, model)
        self.list_schema = self._set_schema(list_schema, model)

        self.create_schema = self._set_schema(create_schema, model)
        if self.create_schema:
            self.create_response_schema = self._get_create_response_schema(model)
        else:
            self.create_response_schema = None

        self.update_schema = self._set_schema(update_schema, model)
        if self.update_schema:
            self.partial_update_schema = PatchDict[self.update_schema]  # type: ignore[misc,name-defined]
        else:
            self.partial_update_schema = None

        # Set or generate the paths
        pk_name = self._get_pk_name(model)
        pk_string = f"{{{pk_name}}}"
        self.create_path: str = create_path or f"{base_path}"
        self.get_one_path: str = get_one_path or f"{base_path}/{pk_string}"
        self.update_path: str = update_path or f"{base_path}/{pk_string}"
        self.delete_path: str = delete_path or f"{base_path}/{pk_string}"
        self.list_path: str = list_path or f"{base_path}"

        # Set or generate the OpenAPI operation IDs
        self.create_operation_id: str = (
            create_operation_id or f"{model.__name__}_create"
        )
        self.update_operation_id: str = (
            update_operation_id or f"{model.__name__}_update"
        )
        self.partial_update_operation_id: str = (
            partial_update_operation_id or f"{model.__name__}_partial_update"
        )
        self.get_one_operation_id: str = (
            get_one_operation_id or f"{model.__name__}_get_one"
        )
        self.list_operation_id: str = list_operation_id or f"{model.__name__}_list"
        self.delete_operation_id: str = (
            delete_operation_id or f"{model.__name__}_delete"
        )

        # Tags
        self.tags: list[str] = [model.__name__]

        # Permissions
        self.permission_classes: list[type[BasePermission[TDjangoModel]]] | None
        self.permission_classes = permission_classes

        super().__init__()

    @overload
    @staticmethod
    def _set_schema(schema_def: None, model: type[TDjangoModel]) -> None: ...  # noqa: E704

    @overload
    @staticmethod
    def _set_schema(  # noqa: E704
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
    def _get_pk_name(
        model_class: type[TDjangoModel],
    ) -> str:
        pk = model_class._meta.pk  # noqa: SLF001  # pyright: ignore [reportUnknownMemberType,reportUnknownVariableType]
        if pk is None:
            # TODO(phuongfi91): Is this unreachable?
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            msg = f"Model {model_class.__name__} doesn't have a primary key"
            raise ValueError(msg)
        return pk.name

    @classmethod
    def _get_create_response_schema(
        cls,
        model_class: type[TDjangoModel],
    ) -> type[BaseSchema[TDjangoModel]]:
        """Get CREATE response schema."""

        @final
        class CreateResponseSchema(BaseSchema[TDjangoModel]):  # noqa: WPS431  # pyright: ignore [reportGeneralTypeIssues, reportUninitializedInstanceVariable]
            config: SchemaConfig[TDjangoModel] = SchemaConfig[TDjangoModel](  # pyright: ignore [reportGeneralTypeIssues]
                model=model_class,
                # TODO(phuongfi91): Check if using "pk" would work instead of "id"
                #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
                fields=["id"],
                name=f"Create{model_class.__name__}Response",
            )

        return CreateResponseSchema
