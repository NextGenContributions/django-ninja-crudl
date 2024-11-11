"""CRUDL API base class."""

from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import (
    ForeignKey,
    ForeignObjectRel,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneField,
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
from pydantic import BaseModel

from django_ninja_crudl.base import CrudlBaseMixin
from django_ninja_crudl.errors.openapi_extras import (
    not_authorized_openapi_extra,
    throttle_openapi_extra,
)
from django_ninja_crudl.errors.schemas import (
    Conflict409Schema,
    ErrorSchema,
    Forbidden403Schema,
    ResourceNotFound404Schema,
    ServiceUnavailable503Schema,
    Unauthorized401Schema,
    UnprocessableEntity422Schema,
)
from django_ninja_crudl.model_utils import get_pydantic_fields
from django_ninja_crudl.types import PathArgs, RequestDetails
from django_ninja_crudl.utils import add_function_arguments, validating_manager
from superschema import Infer, ModelFields, SuperSchema

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager


class CrudlApiBaseMeta:
    """Base meta class for the CRUDL API configuration."""

    create_fields: ClassVar[ModelFields | None] = None
    update_fields: ClassVar[ModelFields | None] = None
    get_one_fields: ClassVar[ModelFields | None] = None
    list_fields: ClassVar[ModelFields | None] = None


DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)


class CrudlMeta[TDjangoModel](type):
    """Metaclass for the CRUDL API."""

    @classmethod
    def _get_pk_name(cls, model_class: type[TDjangoModel]) -> str:
        return model_class._meta.pk.name

    @classmethod
    def _get_pk_type(cls, model_class: type[TDjangoModel]) -> str:
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
        permission_classes = getattr(_meta, "permission_classes", [])

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
                **not_authorized_openapi_extra,
                **throttle_openapi_extra,
            },
        }

        name = model_class.__name__.lower()
        tags = [name]

        @api_controller(tags=tags)
        class CrudlBase[TDjangoModelBase: models.Model](
            ControllerBase,
            CrudlBaseMixin,
        ):
            """Base class for the CRUDL API."""

            _permission_classes = permission_classes

            def _get_related_model(self, field_name: str) -> type[Model]:
                """Return the related model class for a field name."""
                field = model_class._meta.get_field(field_name)  # noqa: SLF001
                if isinstance(field, ForeignObjectRel):
                    return cast(type[Model], field.related_model)
                if isinstance(field, OneToOneRel):
                    return cast(type[Model], field.related_model)
                if isinstance(field, ManyToManyRel):
                    return cast(type[Model], field.related_model)
                if isinstance(field, ManyToOneRel):
                    return cast(type[Model], field.related_model)
                if isinstance(field, ManyToManyField):
                    return cast(type[Model], field.related_model)

                msg = f"Field name '{field_name}' and type '{type(field)}' is not a relation"
                raise ValueError(msg)

            def get_model_filter_args(
                self,
                path_args: dict[str, Any] | None,
            ) -> dict[str, str | int | float | UUID]:
                """Filter out the keys that are not fields of the model."""
                if path_args is None:
                    return {}
                return {
                    k: v for k, v in path_args.items() if getattr(model_class, k, None)
                }

            def get_pre_filtered_queryset(
                self,
                path_args: PathArgs,
            ) -> "BaseManager[Model]":
                """Return a queryset that is filtered by params from the path query."""
                model_filters = self.get_model_filter_args(path_args)
                return self.get_queryset().filter(**model_filters)

            def get_queryset(self) -> "BaseManager[Model]":
                """Return the model's manager."""
                return model_class.objects

            def get_filtered_queryset_for_related_model(
                self,
                request: HttpRequest,
                field_name: str,
                payload: BaseModel | None,
                path_args: PathArgs,
            ) -> models.Q:
                """Get filtered queryset for related model based on custom conditions."""
                # Get the appropriate filtering method based on the field name
                filter_method_name = f"get_related_filter_for_field_{field_name}"
                filter_method = getattr(self, filter_method_name, None)
                if not filter_method:
                    msg = f"Filter method {filter_method_name} not found"
                    raise ValueError(msg)

                return filter_method(request, field_name)

            if create_fields:

                @http_post(
                    path=create_path,
                    operation_id=create_operation_id,
                    tags=tags,
                    response={
                        status.HTTP_201_CREATED: CreateResponseSchema,
                        status.HTTP_401_UNAUTHORIZED: Unauthorized401Schema,
                        status.HTTP_403_FORBIDDEN: Forbidden403Schema,
                        status.HTTP_404_NOT_FOUND: ResourceNotFound404Schema,
                        status.HTTP_409_CONFLICT: Conflict409Schema,
                        status.HTTP_422_UNPROCESSABLE_ENTITY: UnprocessableEntity422Schema,
                        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailable503Schema,
                    },
                    openapi_extra=create_schema_extra,
                )
                @transaction.atomic
                @add_function_arguments(create_path)
                def create(
                    self,
                    request: HttpRequest,
                    payload: CreateSchema,
                    **path_args: PathArgs,
                ) -> (
                    tuple[Literal[403], Forbidden403Schema]
                    | tuple[Literal[409], Conflict409Schema]
                    | tuple[Literal[201], Model]
                ):
                    request_details = RequestDetails[model_class](
                        action="create",
                        request=request,
                        schema=CreateSchema,
                        path_args=path_args,
                        payload=payload,
                        model_class=model_class,
                    )
                    """Create a new object."""
                    if not self.has_permission(request_details):
                        return self.get_403_error(request)
                    self.pre_create(request_details)

                    obj_fields_to_set: list[tuple[str, Any]] = []
                    m2m_fields_to_set: list[tuple[str, Any]] = []

                    for field, field_value in payload.model_dump().items():
                        if isinstance(field_value, Enum | IntEnum):
                            field_value = field_value.value  # noqa: PLW2901
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

                            obj_fields_to_set.append((field_name, field_value))
                    try:
                        with validating_manager(model_class):
                            created_obj: Model = model_class.objects.create(
                                **dict(obj_fields_to_set),
                            )
                    # if integrity error, return 409
                    except IntegrityError as integrity_error:
                        transaction.set_rollback(True)
                        return self.get_409_error(request, exception=integrity_error)

                    for m2m_field, m2m_field_value in m2m_fields_to_set:
                        related_model_class = self._get_related_model(m2m_field)

                        if isinstance(m2m_field_value, list):
                            for m2m_field_value_item in m2m_field_value:
                                related_obj = related_model_class.objects.get(
                                    id=m2m_field_value_item,
                                )
                                request_details_related = request_details
                                request_details_related.related_model_class = (
                                    related_model_class
                                )
                                request_details_related.related_object = related_obj
                                if not self.has_related_object_permission(
                                    request_details_related,
                                ):
                                    transaction.set_rollback(True)
                                    return self.get_404_error(request)
                        else:
                            related_obj = related_model_class.objects.get(
                                id=m2m_field_value,
                            )

                            if not self.has_related_object_permission(request_details):
                                transaction.set_rollback(True)
                                return self.get_404_error(request)

                        try:
                            getattr(created_obj, m2m_field).set(m2m_field_value)
                        except IntegrityError:
                            transaction.set_rollback(True)
                            return self.get_409_error(request)

                    # Perform full_clean() on the created object and raise an exception if it fails
                    try:
                        created_obj.full_clean()
                    except ValidationError as validation_error:
                        # revert the transaction
                        transaction.set_rollback(True)
                        return self.get_409_error(request, exception=validation_error)

                    request_details.object = created_obj
                    self.post_create(request_details)
                    return 201, created_obj

            if get_one_fields:

                @http_get(
                    path=get_one_path,
                    response={
                        status.HTTP_200_OK: GetOneSchema,
                        status.HTTP_401_UNAUTHORIZED: Unauthorized401Schema,
                        status.HTTP_403_FORBIDDEN: Forbidden403Schema,
                        status.HTTP_404_NOT_FOUND: ErrorSchema,
                        status.HTTP_422_UNPROCESSABLE_ENTITY: UnprocessableEntity422Schema,
                        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailable503Schema,
                    },
                    operation_id=get_one_operation_id,
                )
                @add_function_arguments(get_one_path)
                def get_one(
                    self,
                    request: HttpRequest,
                    **path_args: PathArgs,
                ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
                    """Retrieve an object."""
                    request_details = RequestDetails(
                        action="get_one",
                        request=request,
                        schema=GetOneSchema,
                        path_args=path_args,
                        model_class=model_class,
                    )
                    if not self.has_permission(request_details):
                        return self.get_403_error(request)
                    obj = (
                        self.get_pre_filtered_queryset(path_args)
                        .filter(self.get_base_filter(request_details))
                        .filter(self.get_filter_for_get_one(request_details))
                        .first()
                    )
                    if obj is None:
                        return self.get_404_error(request)
                    request_details.object = obj
                    if not self.has_object_permission(request_details):
                        return self.get_404_error(request)
                    return obj

            if update_fields:

                @http_put(
                    path=update_path,
                    operation_id=update_operation_id,
                    response={
                        status.HTTP_200_OK: UpdateSchema,
                        status.HTTP_401_UNAUTHORIZED: Unauthorized401Schema,
                        status.HTTP_403_FORBIDDEN: Forbidden403Schema,
                        status.HTTP_404_NOT_FOUND: ErrorSchema,
                        status.HTTP_422_UNPROCESSABLE_ENTITY: UnprocessableEntity422Schema,
                        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailable503Schema,
                    },
                )
                @transaction.atomic
                @add_function_arguments(update_path)
                def update(
                    self,
                    request: HttpRequest,
                    payload: UpdateSchema,
                    **path_args: PathArgs,
                ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
                    """Update an object."""
                    request_details = RequestDetails[TDjangoModel](
                        action="put",
                        request=request,
                        schema=UpdateSchema,
                        path_args=path_args,
                        payload=payload,
                        model_class=model_class,
                    )
                    if not self.has_permission(request_details):
                        return self.get_403_error(request)
                    obj = (
                        self.get_pre_filtered_queryset(path_args)
                        .filter(self.get_base_filter(request_details))
                        .filter(self.get_filter_for_update(request_details))
                        .first()
                    )

                    if obj is None:
                        return self.get_404_error(request)
                    request_details.object = obj
                    if not self.has_object_permission(request_details):
                        self.get_404_error(request)
                    self.pre_update(request_details)

                    for attr_name, attr_value in payload.model_dump().items():
                        setattr(obj, attr_name, attr_value)
                    obj.save()
                    self.post_update(request_details)
                    return obj

            if update_fields:

                @http_patch(
                    path=update_path,
                    operation_id=patch_operation_id,
                    response={
                        status.HTTP_200_OK: UpdateSchema,
                        status.HTTP_401_UNAUTHORIZED: Unauthorized401Schema,
                        status.HTTP_403_FORBIDDEN: Forbidden403Schema,
                        status.HTTP_404_NOT_FOUND: ResourceNotFound404Schema,
                        status.HTTP_422_UNPROCESSABLE_ENTITY: UnprocessableEntity422Schema,
                        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailable503Schema,
                    },
                    exclude_unset=True,
                )
                @transaction.atomic
                @add_function_arguments(update_path)
                def patch(
                    self,
                    request: HttpRequest,
                    payload: PartialUpdateSchema,
                    **path_args: PathArgs,
                ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
                    """Patch an object."""
                    request_details = RequestDetails[TDjangoModel](
                        action="patch",
                        request=request,
                        schema=PartialUpdateSchema,
                        path_args=path_args,
                        payload=payload,
                        model_class=model_class,
                    )
                    if not self.has_permission(request_details):
                        return self.get_403_error(request)
                    obj: Model | None = (
                        self.get_pre_filtered_queryset(path_args)
                        .filter(self.get_base_filter(request_details))
                        .filter(self.get_filter_for_update(request_details))
                        .first()
                    )
                    if obj is None:
                        return self.get_404_error(request)
                    request_details.object = obj
                    if not self.has_object_permission(request_details):
                        return self.get_404_error(request)

                    for attr_name, attr_value in payload.items():
                        setattr(obj, attr_name, attr_value)
                    obj.save()
                    self.post_patch(request_details)
                    return obj

            @http_delete(
                path=delete_path,
                operation_id=delete_operation_id,
                tags=tags,
                response={
                    status.HTTP_204_NO_CONTENT: None,
                    status.HTTP_401_UNAUTHORIZED: Unauthorized401Schema,
                    status.HTTP_403_FORBIDDEN: Forbidden403Schema,
                    status.HTTP_404_NOT_FOUND: ResourceNotFound404Schema,
                    status.HTTP_422_UNPROCESSABLE_ENTITY: UnprocessableEntity422Schema,
                    status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailable503Schema,
                },
            )
            @transaction.atomic
            @add_function_arguments(delete_path)
            def delete(
                self,
                request: HttpRequest,
                **path_args: PathArgs,
            ) -> tuple[Literal[403, 404], ErrorSchema] | tuple[Literal[204], None]:
                """Delete the object by id."""
                request_details = RequestDetails[TDjangoModel](
                    action="delete",
                    request=request,
                    path_args=path_args,
                    model_class=model_class,
                )
                if not self.has_permission(request_details):
                    return self.get_403_error(request)

                obj = (
                    self.get_pre_filtered_queryset(path_args)
                    .filter(self.get_filter_for_delete(request_details))
                    .first()
                )
                if obj is None:
                    return self.get_404_error(request)
                request_details.object = obj
                if not self.has_object_permission(request_details):
                    return self.get_404_error(request)
                self.pre_delete(request_details)
                obj.delete()
                self.post_delete(request_details)
                return 204, None

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
                    response={
                        200: list[ListSchema],
                        401: Unauthorized401Schema,
                        status.HTTP_403_FORBIDDEN: Forbidden403Schema,
                        422: UnprocessableEntity422Schema,
                        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailable503Schema,
                    },
                    operation_id=list_operation_id,
                    tags=tags,
                    openapi_extra=openapi_extra,
                )
                # @paginate
                # @searching(Searching, search_fields=search_fields)
                @add_function_arguments(list_path)
                def get_many(
                    self,
                    request: HttpRequest,
                    response: HttpResponse,
                    **path_args: PathArgs,
                ) -> tuple[Literal[403], ErrorSchema] | models.Manager[Model]:
                    """List all objects."""
                    request_details = RequestDetails[TDjangoModel](
                        action="list",
                        request=request,
                        path_args=path_args,
                        model_class=model_class,
                    )

                    if not self.has_permission(request_details):
                        return self.get_403_error(request)

                    qs = (
                        self.get_pre_filtered_queryset(path_args)
                        .filter(self.get_base_filter(request_details))
                        .filter(self.get_filter_for_list(request_details))
                    )

                    # Return the total count of objects in the response headers
                    response["x-total-count"] = qs.count()

                    # Extract the related models from the ListSchema fields
                    related_models: list[str] = []
                    many_to_many_models: list[str] = []
                    related_fields: list[str] = []
                    for field_name, field in ListSchema.model_fields.items():
                        django_field = model_class._meta.get_field(field_name)  # noqa: SLF001
                        if isinstance(
                            django_field,
                            OneToOneField | ForeignKey,
                        ):
                            related_models.append(field_name)
                            related_fields.extend(
                                get_pydantic_fields(
                                    ListSchema,
                                    field_name,
                                ),
                            )

                        elif isinstance(
                            django_field,
                            ManyToManyField,
                        ):
                            many_to_many_models.append(field_name)
                            related_fields.extend(
                                get_pydantic_fields(
                                    ListSchema,
                                    field_name,
                                ),
                            )
                            # related_models.append(f"{field_name}__id")

                    non_related_fields: list[str] = [
                        field_name
                        for field_name in ListSchema.model_fields.keys()
                        if field_name not in related_models + many_to_many_models
                    ]

                    all_fields: list[str] = non_related_fields + related_fields

                    qs = qs.select_related(*related_models).prefetch_related(
                        *many_to_many_models,
                    )  # To avoid N+1 queries
                    qs = qs.values(*all_fields)
                    print(qs.query)
                    print(qs.all())
                    return qs

        for attr_name, attr_value in CrudlBase.__dict__.items():
            if not attr_name.startswith("__"):
                dct[attr_name] = attr_value

        # Add ControllerBase as a base class
        bases = (ControllerBase,)

        return super().__new__(cls, name, bases, dct)


class Crudl(CrudlBaseMixin, metaclass=CrudlMeta):
    """Base class for the CRUDL API."""

    class Meta:
        """Configuration for the CRUDL API."""

        abstract = True
