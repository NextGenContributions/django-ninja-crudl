"""CRUDL API base class."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, ClassVar, Literal
from uuid import UUID

from django.db import models, transaction
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from django.http import HttpRequest, HttpResponse
from ninja import PatchDict
from ninja_extra import (
    ControllerBase,
    api_controller,
    http_delete,
    http_get,
    http_patch,
    http_post,
    http_put,
    status,
)
from ninja_extra.searching import Searching, searching

from django_ninja_crudl.errors import (
    Conflict409Schema,
    ErrorSchema,
    ResourceNotFound404Schema,
)
from superschema import Infer, ModelFields, SuperSchema

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager

FKwargs = dict[str, Any]


def extract_arguments_from_path_spec(path_spec: str) -> dict[str, type]:
    """Extract arguments from the path spec.

    Args:
        path_spec (str): The path spec. For example: "/{uuid:organization}/resource/{uuid:id}"

    Returns:
        dict[str, type]: A dictionary with the argument names as keys and the argument types as values. For example: {"organization": UUID, "id": UUID}.

    """
    args_with_types: dict[str, type] = {}
    for part in path_spec.split("/"):
        if part.startswith("{") and part.endswith("}"):
            arg_type, arg_name = part[1:-1].split(":")
            if arg_type == "uuid":
                arg_type = UUID
            elif arg_type == "int":
                arg_type = int
            elif arg_type == "str":
                arg_type = str
            args_with_types[arg_name] = arg_type
    return args_with_types


def add_function_arguments(path_spec: str) -> Callable[[Callable], Callable]:
    """Add function arguments to the decorated function."""
    new_args_with_types: dict[str, type] = extract_arguments_from_path_spec(path_spec)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        new_signature = inspect.signature(func)

        # add the new arguments to the signature before the **kwargs:
        new_params = list(new_signature.parameters.values())
        new_params = (
            new_params[:-1]
            + [
                inspect.Parameter(
                    name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=new_args_with_types[name],
                )
                for name in new_args_with_types
            ]
            + new_params[-1:]
        )
        new_signature = new_signature.replace(parameters=new_params)

        wrapper.__signature__ = new_signature
        return wrapper

    return decorator


class CrudlApiBaseMeta:
    """Base meta class for the CRUDL API configuration."""

    create_fields: ClassVar[ModelFields | None] = None
    update_fields: ClassVar[ModelFields | None] = None
    get_one_fields: ClassVar[ModelFields | None] = None
    list_fields: ClassVar[ModelFields | None] = None


DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)


class CrudlMeta(type):
    """Metaclass for the CRUDL API."""

    @classmethod
    def _get_pk_name(cls, model_class: type[Model]) -> str:
        return model_class._meta.pk.name

    @classmethod
    def _get_pk_type(cls, model_class: type[Model]) -> str:
        """Get the primary key type."""
        field = model_class._meta.pk
        if isinstance(
            field,
            models.AutoField | models.BigAutoField | models.SmallAutoField,
        ):
            return "int"
        if isinstance(field, models.UUIDField):
            return "uuid"
        msg = f"Unknown primary key type: {field}"
        raise TypeError(msg)

    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> type:
        """Create a new class."""
        # quit if this is the base class
        if name == "Crudl":
            return super().__new__(cls, name, bases, dct)

        _meta = dct.get("Meta")

        model_class: type[Model] = _meta.model_class

        api_meta = getattr(model_class, "CrudlApiMeta", None)
        if api_meta is None:
            msg = f"CrudlApiMeta is required for model '{name}'"
            raise ValueError(msg)

        if issubclass(api_meta, CrudlApiBaseMeta):
            create_fields: ModelFields | None = api_meta.create_fields
            update_fields: ModelFields | None = api_meta.update_fields
            get_one_fields: ModelFields | None = api_meta.get_one_fields
            list_fields: ModelFields | None = api_meta.list_fields
            search_fields: list[str] | None = getattr(api_meta, "search_fields", None)
        else:
            msg = f"CrudlApiMeta class of '{name}' needs to inherit CrudlApiBaseMeta"
            raise TypeError(msg)

        pk_name = cls._get_pk_name(model_class)
        pk_type = cls._get_pk_type(model_class)

        if getattr(_meta, "base_path", None) is None or not isinstance(
            _meta.base_path,
            str,
        ):
            msg = f"base_path is required for model '{name}'"
            raise ValueError(msg)

        base_path = _meta.base_path

        resource_name = model_class.__name__.lower()

        id_string = f"{{{pk_type}:{pk_name}}}"
        create_path = f"{base_path}/"
        get_one_path = f"{base_path}/{id_string}"
        get_one_path_with_pk = f"{base_path}/{{id}}"
        update_path = f"{base_path}/{id_string}"
        delete_path = f"{base_path}/{id_string}"
        list_path = f"{base_path}/"

        create_operation_id = f"{name}_create"
        get_one_operation_id = f"{name}_retrieve"
        update_operation_id = f"{name}_update"
        patch_operation_id = f"{name}_partial_update"
        delete_operation_id = f"{name}_delete"
        list_operation_id = f"{name}_list"

        class PathId(SuperSchema):
            class Meta(SuperSchema.Meta):
                model = model_class
                name = f"{model_class.__name__}_PathId"
                fields = {pk_name: Infer}

        class CreateSchema(SuperSchema):
            """Create schema for the model."""

            class Meta(SuperSchema.Meta):
                """Pydantic configuration."""

                name = f"{model_class.__name__}_Create"
                model = model_class
                fields = create_fields if create_fields else None

        class GetOneSchema(SuperSchema):
            """Get one schema for the model."""

            class Meta(SuperSchema.Meta):
                """Pydantic configuration."""

                name = f"{model_class.__name__}_GetOne"
                model = model_class
                fields = get_one_fields if get_one_fields else None

        class UpdateSchema(SuperSchema):
            """Update schema for the model."""

            class Meta(SuperSchema.Meta):
                """Pydantic configuration."""

                name = f"{model_class.__name__}_Update"
                model = model_class
                fields = update_fields if update_fields else None

        PartialUpdateSchema = PatchDict[UpdateSchema]

        class ListSchema(SuperSchema):
            """List schema for the model."""

            class Meta(SuperSchema.Meta):
                """Pydantic configuration."""

                name = f"{model_class.__name__}_List"
                model = model_class
                fields = list_fields if list_fields else None

        create_response_name = f"{model_class.__name__}_CreateResponse"

        class CreateResponseSchema(SuperSchema):
            """Response schema for the create operation.

            Only the id field is returned.
            """

            class Meta(SuperSchema.Meta):
                """Pydantic configuration."""

                name = create_response_name
                model = model_class
                fields: ClassVar[ModelFields | None] = {"id": Infer}

        create_schema_extra = {
            "responses": {
                201: {
                    "description": "Created",
                    "content": {
                        "application/json": {
                            # "schema": CreateResponseSchema.model_json_schema(),
                            "schema": {
                                "$ref": f"#/components/schemas/{create_response_name}",
                            },
                        },
                    },
                    "links": {
                        "UpdateById": {
                            "operationId": update_operation_id,
                            "parameters": {"id": "$response.body#/id"},
                            "description": f"Update {resource_name} by id",
                        },
                        "DeleteById": {
                            "operationId": delete_operation_id,
                            "parameters": {"id": "$response.body#/id"},
                            "description": f"Delete {resource_name} by id",
                        },
                        "GetById": {
                            "operationId": get_one_operation_id,
                            "parameters": {"id": "$response.body#/id"},
                            "description": f"Get {resource_name} by id",
                        },
                        "PatchById": {
                            "operationId": patch_operation_id,
                            "parameters": {"id": "$response.body#/id"},
                            "description": f"Patch {resource_name} by id",
                        },
                    },
                },
            },
        }

        name = model_class.__name__.lower()
        tags = [name]

        @api_controller(tags=tags)
        class CrudlBase(ControllerBase):
            """Base class for the CRUDL API."""

            def _check_permissions(
                self,
                request: HttpRequest,
                type: str,
                model_class: type[models.Model],
            ) -> None:
                """Check the permissions for the object."""

            def _check_object_permissions(
                self,
                request: HttpRequest,
                type: str,
                obj: models.Model,
            ) -> None:
                pass

            def get_model_filter_args(
                self,
                kwargs: dict[str, Any] | None,
            ) -> dict[str, str | int | float | UUID]:
                """Filter out the keys that are not fields of the model."""
                if kwargs is None:
                    return {}
                return {
                    k: v for k, v in kwargs.items() if getattr(model_class, k, None)
                }

            def get_pre_filtered_queryset(
                self,
                kwargs: dict[str, Any],
            ) -> "BaseManager[Model]":
                """Return a queryset that is filtered by params from the path query."""
                model_filters = self.get_model_filter_args(kwargs)
                qs = self.get_queryset().filter(**model_filters)
                return qs

            def get_queryset(self) -> "BaseManager[Model]":
                """Return the model's manager."""
                return model_class.objects

            if create_fields:

                @http_post(
                    path=create_path,
                    operation_id=create_operation_id,
                    tags=tags,
                    response={
                        status.HTTP_201_CREATED: CreateResponseSchema,
                        status.HTTP_404_NOT_FOUND: ResourceNotFound404Schema,
                        status.HTTP_409_CONFLICT: Conflict409Schema,
                    },
                    openapi_extra=create_schema_extra,
                )
                @transaction.atomic
                @add_function_arguments(create_path)
                def create(
                    self,
                    request: HttpRequest,
                    payload: CreateSchema,
                    **kwargs: FKwargs,
                ) -> tuple[Literal[201], Model]:
                    """Create a new object."""
                    obj = model_class()
                    self.check_object_permissions(obj)

                    m2m_fields_to_set: list[tuple[str, Any]] = []
                    for field, field_value in payload.model_dump().items():
                        print("----------###########field", field)
                        if isinstance(
                            model_class._meta.get_field(field),  # noqa: SLF001, WPS437
                            ManyToManyField
                            | ManyToManyRel
                            | ManyToOneRel
                            | OneToOneRel,
                        ):
                            m2m_fields_to_set.append((field, field_value))
                        else:
                            # Handle foreign key fields:
                            if isinstance(
                                model_class._meta.get_field(field),  # noqa: SLF001, WPS437
                                ForeignKey,
                            ) and not field.endswith("_id"):
                                field_name = f"{field}_id"
                            else:  # Non-relational fields
                                field_name = field

                            setattr(obj, field_name, field_value)

                    obj.save()

                    for m2m_field, m2m_field_value in m2m_fields_to_set:
                        """
                        self._check_permissions(
                            request=request,
                            type="create",
                            model_class=getattr(model_class, m2m_field).related_model,
                        )
                        """
                        getattr(obj, m2m_field).set(m2m_field_value)

                    return status.HTTP_201_CREATED, obj

            if get_one_fields:

                @http_get(
                    path=get_one_path,
                    # path=get_one_path_with_pk,
                    response={
                        status.HTTP_200_OK: GetOneSchema,
                        status.HTTP_404_NOT_FOUND: ErrorSchema,
                    },
                    operation_id=get_one_operation_id,
                )
                @add_function_arguments(get_one_path)
                def get_one(
                    self,
                    **kwargs: FKwargs,
                ) -> tuple[Literal[404], ErrorSchema] | Model:
                    """Retrieve an object."""
                    # kwargs["id"] = id.id
                    obj = self.get_pre_filtered_queryset(kwargs).first()
                    if obj is None:
                        return status.HTTP_404_NOT_FOUND, ErrorSchema(
                            code="not_found",
                            message="Not found",
                        )
                    return obj

            if update_fields:

                @http_put(
                    path=update_path,
                    operation_id=update_operation_id,
                    response={
                        status.HTTP_200_OK: UpdateSchema,
                        status.HTTP_404_NOT_FOUND: ErrorSchema,
                    },
                )
                @transaction.atomic
                @add_function_arguments(update_path)
                def update(
                    self,
                    payload: UpdateSchema,
                    **kwargs: FKwargs,
                ) -> tuple[Literal[404], ErrorSchema] | Model:
                    """Update an object."""
                    obj = self.get_pre_filtered_queryset(kwargs).first()

                    if obj is None:
                        return status.HTTP_404_NOT_FOUND, ErrorSchema(
                            code="not_found",
                            message="Not found",
                        )

                    for attr_name, attr_value in payload.model_dump().items():
                        setattr(obj, attr_name, attr_value)
                    obj.save()
                    return obj

            if update_fields:

                @http_patch(
                    path=update_path,
                    operation_id=patch_operation_id,
                    response={
                        status.HTTP_200_OK: UpdateSchema,
                        status.HTTP_404_NOT_FOUND: ResourceNotFound404Schema,
                    },
                    exclude_unset=True,
                )
                @transaction.atomic
                @add_function_arguments(update_path)
                def patch(
                    self,
                    payload: PartialUpdateSchema,
                    **kwargs: FKwargs,
                ) -> tuple[Literal[404], ErrorSchema] | Model:
                    obj: Model | None = self.get_pre_filtered_queryset(kwargs).first()
                    if obj is None:
                        return status.HTTP_404_NOT_FOUND, ErrorSchema(
                            code="not_found",
                            message="Not found",
                        )

                    for attr_name, attr_value in payload.items():
                        setattr(obj, attr_name, attr_value)
                    obj.save()
                    return obj

            @http_delete(
                path=delete_path,
                operation_id=delete_operation_id,
                tags=tags,
                response={
                    status.HTTP_204_NO_CONTENT: None,
                    status.HTTP_404_NOT_FOUND: ResourceNotFound404Schema,
                },
            )
            @add_function_arguments(delete_path)
            def delete(
                self,
                **kwargs: FKwargs,
            ) -> tuple[Literal[404], ErrorSchema] | tuple[Literal[204], None]:
                """Delete the object by id."""
                obj = self.get_pre_filtered_queryset(kwargs).first()
                if obj is None:
                    return status.HTTP_404_NOT_FOUND, ErrorSchema(
                        code="not_found",
                        message="Not found",
                    )
                obj.delete()
                return status.HTTP_204_NO_CONTENT, None

            if list_fields:
                openapi_extra = {
                    "responses": {
                        status.HTTP_200_OK: {
                            "description": "Successful response",
                            "headers": {
                                "x-total-count": {
                                    "schema": {
                                        "type": "integer",
                                        "minimum": 0,
                                    },
                                    "description": "Total number of items",
                                },
                            },
                        },
                    },
                }

                @http_get(
                    path=list_path,
                    response=list[ListSchema],
                    operation_id=list_operation_id,
                    tags=tags,
                    openapi_extra=openapi_extra,
                )
                # @paginate
                @searching(Searching, search_fields=search_fields)
                @add_function_arguments(list_path)
                def get_many(
                    self,
                    request: HttpRequest,
                    response: HttpResponse,
                    **kwargs: FKwargs,
                ) -> models.Manager[Model]:
                    """List all objects."""
                    # qs = self.get_pre_filtered_queryset(kwargs)
                    qs = self.get_queryset()

                    # Return the total count of objects in the response headers
                    response["x-total-count"] = qs.count()

                    return qs

        for attr_name, attr_value in CrudlBase.__dict__.items():
            if not attr_name.startswith("__"):
                dct[attr_name] = attr_value

        # Add ControllerBase as a base class
        bases = (ControllerBase,)

        return super().__new__(cls, name, bases, dct)


class Crudl(metaclass=CrudlMeta):
    """Base class for the CRUDL API."""

    class Meta:
        """Configuration for the CRUDL API."""

        abstract = True
