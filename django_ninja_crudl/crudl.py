# TODO(phuongfi91): Double check and then fully remove this file

# """CRUDL API base class."""
#
# import logging
# from abc import ABC, ABCMeta
# from enum import Enum, IntEnum
# from typing import TYPE_CHECKING, Any, Generic, Literal, cast
# from uuid import UUID
#
# from beartype import beartype
# from django.core.exceptions import ValidationError
# from django.db import IntegrityError, models, transaction
# from django.db.models import (
#     ForeignKey,
#     ForeignObjectRel,
#     ManyToManyField,
#     ManyToManyRel,
#     ManyToOneRel,
#     Model,
#     OneToOneField,
#     OneToOneRel,
# )
# from django.http import HttpRequest, HttpResponse
# from ninja import PatchDict
# from ninja_extra import api_controller  # pyright: ignore[reportUnknownVariableType]
# from ninja_extra import (
#     ControllerBase,
#     http_delete,
#     http_get,
#     http_patch,
#     http_post,
#     http_put,
#     status,
# )
# from pydantic import BaseModel
#
# from django_ninja_crudl import CrudlConfig
# from django_ninja_crudl.base import CrudlBaseMethodsMixin
# from django_ninja_crudl.errors.openapi_extras import (
#     not_authorized_openapi_extra,
#     throttle_openapi_extra,
# )
# from django_ninja_crudl.errors.schemas import (
#     Error401UnauthorizedSchema,
#     Error403ForbiddenSchema,
#     Error404NotFoundSchema,
#     Error409ConflictSchema,
#     Error422UnprocessableEntitySchema,
#     Error503ServiceUnavailableSchema,
#     ErrorSchema,
# )
# from django_ninja_crudl.model_utils import get_pydantic_fields
# from django_ninja_crudl.types import JSON, PathArgs, RequestDetails, TDjangoModel_co
# from django_ninja_crudl.utils import add_function_arguments, validating_manager
#
# if TYPE_CHECKING:
#     from django.db.models.manager import Manager
#
# logger: logging.Logger = logging.getLogger("django_ninja_crudl")
#
#
# DjangoRelationFields = (
#     ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
# )
#
#
# @beartype
# class CrudlMeta(ABCMeta):
#     """Metaclass for the CRUDL API."""
#
#     def __new__(
#         cls, name: str, bases: tuple[type[object], ...], dct: dict[str, Any]
#     ) -> type[object]:
#         """Create a new class."""
#         # quit if this is an abstract base class
#         if not dct.get("config"):
#             return super().__new__(cls, name, bases, dct)
#
#         config = dct.get("config")
#
#         if not config or not isinstance(config, CrudlConfig):
#             class_name = __name__
#             config_module = f"{CrudlConfig.__module__}.{CrudlConfig.__qualname__}"
#             print(bases)
#             msg = (
#                 f"Class '{class_name}' must have a 'config' attribute, "
#                 f" which must be an instance or subclass of {config_module}."
#             )
#             raise ValueError(msg)
#
#         model_class = config.model
#
#         if config.create_schema:
#             create_schema_extra = {}
#
#         if config.update_schema:
#             PartialUpdateSchema = PatchDict[config.update_schema]  # pyright: ignore[reportInvalidTypeArguments]  # noqa: N806 # NOSONAR
#
#         name = model_class.__name__.lower()
#         tags = [name]
#
#         @api_controller(tags=tags)
#         class CrudlBase(
#             Generic[TDjangoModel_co],
#             ControllerBase,
#             CrudlBaseMethodsMixin[TDjangoModel_co],
#             ABC,
#         ):
#             """Base class for the CRUDL API."""
#
#             if config.create_schema:
#                 payload = config.create_schema
#
#                 @http_post(
#                     path=config.create_path,
#                     operation_id=config.create_operation_id,
#                     tags=tags,
#                     response={
#                         status.HTTP_201_CREATED: config.create_schema,  # pyright: ignore[reportPossiblyUnboundVariable]
#                         status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
#                         status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
#                         status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
#                         status.HTTP_409_CONFLICT: Error409ConflictSchema,
#                         status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
#                         status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
#                     },
#                     openapi_extra=create_schema_extra,
#                     by_alias=True,
#                 )
#                 @transaction.atomic
#                 @add_function_arguments(config.create_path)
#                 def create(
#                     self,
#                     request: HttpRequest,
#                     payload: payload,
#                     **path_args: PathArgs,
#                 ) -> tuple[Literal[403, 409], ErrorSchema] | tuple[Literal[201], Model]:
#                     """Create a new object."""
#                     request_details = RequestDetails[Model](
#                         action="create",
#                         request=request,
#                         schema=config.create_schema,
#                         path_args=path_args,
#                         payload=payload,
#                         model_class=model_class,
#                     )
#                     if not self.has_permission(request_details):
#                         return self.get_403_error(request)  # noqa: WPS220
#                     self.pre_create(request_details)
#
#                     obj_fields_to_set: list[tuple[str, Any]] = []  # pyright: ignore[reportExplicitAny]
#                     m2m_fields_to_set: list[tuple[str, Any]] = []  # pyright: ignore[reportExplicitAny]
#
#                     for field, field_value in payload.model_dump().items():
#                         if isinstance(field_value, Enum | IntEnum):
#                             field_value = field_value.value  # noqa: PLW2901, WPS220
#                         if isinstance(
#                             model_class._meta.get_field(field),  # noqa: SLF001, WPS437
#                             ManyToManyField
#                             | ManyToManyRel
#                             | ManyToOneRel
#                             | OneToOneRel,
#                         ):
#                             m2m_fields_to_set.append((field, field_value))  # noqa: WPS220
#                         else:
#                             # Handle foreign key fields:
#                             if isinstance(  # noqa: WPS220, WPS337
#                                 model_class._meta.get_field(field),  # noqa: SLF001, WPS437
#                                 ForeignKey,
#                             ) and not field.endswith("_id"):
#                                 field_name = f"{field}_id"  # noqa: WPS220
#                             else:  # Non-relational fields
#                                 field_name = field  # noqa: WPS220
#
#                             obj_fields_to_set.append((field_name, field_value))  # noqa: WPS220
#                     try:
#                         with validating_manager(model_class):  # noqa: WPS220
#                             created_obj: Model = model_class.objects.create(
#                                 **dict(obj_fields_to_set),
#                             )
#                     # if integrity error, return 409
#                     except IntegrityError as integrity_error:
#                         transaction.set_rollback(True)
#                         return self.get_409_error(request, exception=integrity_error)
#
#                     for (
#                         m2m_field,
#                         m2m_field_value,
#                     ) in m2m_fields_to_set:  # pyright: ignore[reportAny]
#                         related_model_class = self._get_related_model(m2m_field)
#
#                         if isinstance(m2m_field_value, list):  # noqa: WPS220
#                             for m2m_field_value_item in m2m_field_value:
#                                 related_obj = related_model_class.objects.get(
#                                     id=m2m_field_value_item,
#                                 )
#                                 request_details_related = request_details  # noqa: WPS220
#                                 request_details_related.related_model_class = (
#                                     related_model_class
#                                 )
#                                 request_details_related.related_object = related_obj
#                                 if not self.has_related_object_permission(
#                                     request_details_related,
#                                 ):
#                                     transaction.set_rollback(True)
#                                     return self.get_404_error(request)
#                         else:
#                             related_obj = related_model_class.objects.get(
#                                 id=m2m_field_value,
#                             )
#
#                             if not self.has_related_object_permission(request_details):
#                                 transaction.set_rollback(True)
#                                 return self.get_404_error(request)
#
#                         try:
#                             getattr(created_obj, m2m_field).set(m2m_field_value)
#                         except IntegrityError:
#                             transaction.set_rollback(True)  # noqa: WPS220
#                             return self.get_409_error(request)
#
#                     # Perform full_clean() on the created object
#                     # and raise an exception if it fails
#                     try:
#                         created_obj.full_clean()  # noqa: WPS220
#                     except ValidationError as validation_error:
#                         # revert the transaction
#                         transaction.set_rollback(True)  # noqa: WPS220
#                         return self.get_409_error(request, exception=validation_error)
#
#                     request_details.object = created_obj
#                     self.post_create(request_details)
#                     return 201, created_obj
#
#             if config.get_one_schema:
#
#                 @http_get(
#                     path=config.get_one_path,
#                     response={
#                         status.HTTP_200_OK: config.get_one_schema,
#                         status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
#                         status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
#                         status.HTTP_404_NOT_FOUND: ErrorSchema,
#                         status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
#                         status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
#                     },
#                     operation_id=config.get_one_operation_id,
#                     by_alias=True,
#                 )
#                 @add_function_arguments(config.get_one_path)
#                 def get_one(
#                     self,
#                     request: HttpRequest,
#                     **path_args: PathArgs,
#                 ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
#                     """Retrieve an object."""
#                     request_details = RequestDetails[Model](
#                         action="get_one",
#                         request=request,
#                         schema=config.get_one_schema,
#                         path_args=path_args,
#                         model_class=model_class,
#                     )
#                     if not self.has_permission(request_details):
#                         return self.get_403_error(request)  # noqa: WPS220
#
#                     obj = (
#                         self.get_pre_filtered_queryset(path_args)
#                         .filter(self.get_base_filter(request_details))
#                         .filter(self.get_filter_for_get_one(request_details))
#                         .first()
#                     )
#                     if obj is None:
#                         return self.get_404_error(request)  # noqa: WPS220
#                     request_details.object = obj
#                     if not self.has_object_permission(request_details):
#                         return self.get_404_error(request)  # noqa: WPS220
#                     return obj
#
#             if config.update_schema:
#                 payload_schema = config.update_schema
#
#                 @http_put(
#                     path=config.update_path,
#                     operation_id=config.update_operation_id,
#                     response={
#                         status.HTTP_200_OK: config.update_schema,  # pyright: ignore[reportPossiblyUnboundVariable]
#                         status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
#                         status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
#                         status.HTTP_404_NOT_FOUND: ErrorSchema,
#                         status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
#                         status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
#                     },
#                     by_alias=True,
#                 )
#                 @transaction.atomic
#                 @add_function_arguments(config.update_path)
#                 def update(
#                     self,
#                     request: HttpRequest,
#                     payload: payload_schema,
#                     **path_args: PathArgs,
#                 ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
#                     """Update an object."""
#                     request_details = RequestDetails[Model](
#                         action="put",
#                         request=request,
#                         schema=config.update_schema,
#                         path_args=path_args,
#                         payload=payload,  # pyright: ignore[reportPossiblyUnboundVariable]
#                         model_class=model_class,
#                     )
#                     if not self.has_permission(request_details):
#                         return self.get_403_error(request)  # noqa: WPS220
#                     obj = (
#                         self.get_pre_filtered_queryset(path_args)
#                         .filter(self.get_base_filter(request_details))
#                         .filter(self.get_filter_for_update(request_details))
#                         .first()
#                     )
#
#                     if obj is None:
#                         return self.get_404_error(request)  # noqa: WPS220
#                     request_details.object = obj
#                     if not self.has_object_permission(request_details):
#                         return self.get_404_error(request)  # noqa: WPS220
#                     self.pre_update(request_details)
#
#                     for attr_name, attr_value in payload.model_dump().items():
#                         setattr(obj, attr_name, attr_value)  # noqa: WPS220
#                     obj.save()
#                     self.post_update(request_details)
#                     return obj
#
#             if config.update_schema:
#                 patch_operation_id: str = config.partial_update_operation_id
#
#                 @http_patch(
#                     path=config.update_path,
#                     operation_id=patch_operation_id,
#                     response={
#                         status.HTTP_200_OK: config.update_schema,
#                         status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
#                         status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
#                         status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
#                         status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
#                         status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
#                     },
#                     by_alias=True,
#                 )
#                 @transaction.atomic
#                 @add_function_arguments(config.update_path)
#                 def patch(
#                     self,
#                     request: HttpRequest,
#                     payload: PartialUpdateSchema,  # pyright: ignore[reportInvalidTypeForm, reportUnknownParameterType]
#                     **path_args: PathArgs,
#                 ) -> tuple[Literal[403, 404], ErrorSchema] | Model:
#                     """Partial update an object."""
#                     request_details = RequestDetails[Model](
#                         action="patch",
#                         request=request,
#                         schema=PartialUpdateSchema,  # pyright: ignore[reportPossiblyUnboundVariable]
#                         path_args=path_args,
#                         payload=payload,  # pyright: ignore[reportUnknownArgumentType]
#                         model_class=model_class,
#                     )
#                     if not self.has_permission(request_details):
#                         return self.get_403_error(request)  # noqa: WPS220
#                     obj: Model | None = (
#                         self.get_pre_filtered_queryset(path_args)
#                         .filter(self.get_base_filter(request_details))
#                         .filter(self.get_filter_for_update(request_details))
#                         .first()
#                     )
#                     if obj is None:
#                         return self.get_404_error(request)  # noqa: WPS220
#                     request_details.object = obj
#                     if not self.has_object_permission(request_details):
#                         return self.get_404_error(request)  # noqa: WPS220
#                     self.pre_patch(request_details)
#
#                     for attr_name, attr_value in payload.items():
#                         setattr(obj, attr_name, attr_value)  # noqa: WPS220
#                     obj.save()
#                     self.post_patch(request_details)
#                     return obj
#
#             if config.delete_allowed:
#
#                 @http_delete(
#                     path=config.delete_path,
#                     operation_id=config.delete_operation_id,
#                     tags=tags,
#                     response={
#                         status.HTTP_204_NO_CONTENT: None,
#                         status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
#                         status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
#                         status.HTTP_404_NOT_FOUND: Error404NotFoundSchema,
#                         status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
#                         status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
#                     },
#                     by_alias=True,
#                 )
#                 @transaction.atomic
#                 @add_function_arguments(config.delete_path)
#                 def delete(
#                     self,
#                     request: HttpRequest,
#                     **path_args: PathArgs,
#                 ) -> tuple[Literal[403, 404], ErrorSchema] | tuple[Literal[204], None]:
#                     """Delete the object by id."""
#                     request_details = RequestDetails[Model](
#                         action="delete",
#                         request=request,
#                         path_args=path_args,
#                         model_class=model_class,
#                     )
#                     if not self.has_permission(request_details):
#                         return self.get_403_error(request)  # noqa: WPS220
#
#                     obj = (
#                         self.get_pre_filtered_queryset(path_args)
#                         .filter(self.get_filter_for_delete(request_details))
#                         .first()
#                     )
#                     if obj is None:
#                         return self.get_404_error(request)  # noqa: WPS220
#                     request_details.object = obj
#                     if not self.has_object_permission(request_details):
#                         return self.get_404_error(request)  # noqa: WPS220
#                     self.pre_delete(request_details)
#                     obj.delete()
#                     self.post_delete(request_details)
#                     return 204, None
#
#             if config.list_schema:
#                 openapi_extra: dict[str, Any] = {  # pyright: ignore[reportExplicitAny]
#                     "responses": {
#                         status.HTTP_200_OK: {
#                             "description": "Successful response",
#                             "headers": {
#                                 "x-total-count": {
#                                     "schema": {
#                                         "type": "integer",
#                                         "minimum": 0,
#                                     },
#                                     "description": "Total number of items",
#                                 },
#                             },
#                         },
#                     },
#                 }
#
#                 @http_get(
#                     path=config.list_path,
#                     response={
#                         200: list[config.list_schema],  # pyright: ignore[reportPossiblyUnboundVariable]
#                         401: Error401UnauthorizedSchema,
#                         status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
#                         422: Error422UnprocessableEntitySchema,
#                         status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
#                     },
#                     operation_id=config.list_operation_id,
#                     tags=tags,
#                     openapi_extra=openapi_extra,
#                     by_alias=True,
#                 )
#                 # @paginate
#                 # @searching(Searching, search_fields=search_fields)
#                 @add_function_arguments(config.list_path)
#                 def get_many(  # noqa: WPS210
#                     self,
#                     request: HttpRequest,
#                     response: HttpResponse,
#                     **path_args: PathArgs,
#                 ) -> tuple[int, ErrorSchema] | models.Manager[Model]:
#                     """List all objects."""
#                     request_details = RequestDetails[Model](
#                         action="list",
#                         request=request,
#                         path_args=path_args,
#                         model_class=model_class,
#                     )
#
#                     if not self.has_permission(request_details):
#                         return self.get_403_error(request)  # noqa: WPS220
#
#                     qs = (
#                         self.get_pre_filtered_queryset(path_args)
#                         .filter(self.get_base_filter(request_details))
#                         .filter(self.get_filter_for_list(request_details))
#                     )
#
#                     # Return the total count of objects in the response headers
#                     response["x-total-count"] = qs.count()
#
#                     # Extract the related models from the ListSchema fields
#                     related_models: list[str] = []
#                     many_to_many_models: list[str] = []
#                     related_fields: list[str] = []
#                     property_fields: list[str] = []
#
#                     for field_name in config.list_schema.model_fields:
#                         attr = getattr(model_class, field_name, None)  # noqa: WPS220
#
#                         # Skip @property methods here
#                         if attr and isinstance(attr, property):
#                             property_fields.append(field_name)  # noqa: WPS220
#                             # TODO: Implement a way to avoid N+1 queries when using @property methods
#                             logger.debug(  # noqa: WPS220
#                                 "Detected use of @property method %s of the model %s in"
#                                 " list_fields definition which"
#                                 " may cause N+1 queries and cause performance degradation.",
#                                 field_name,
#                                 model_class,
#                             )
#                             return qs  # noqa: WPS220
#
#                         django_field = model_class._meta.get_field(field_name)  # noqa: SLF001
#                         if isinstance(
#                             django_field,
#                             OneToOneField | ForeignKey,
#                         ):
#                             related_models.append(field_name)  # noqa: WPS220
#                             related_fields.extend(  # noqa: WPS220
#                                 get_pydantic_fields(
#                                     config.list_schema,
#                                     field_name,
#                                 ),
#                             )
#
#                         elif isinstance(  # noqa: WPS220
#                             django_field,
#                             ManyToManyField,
#                         ):
#                             many_to_many_models.append(field_name)  # noqa: WPS220
#                             related_fields.extend(  # noqa: WPS220
#                                 get_pydantic_fields(
#                                     config.list_schema,
#                                     field_name,
#                                 ),
#                             )
#                             # related_models.append(f"{field_name}__id")
#
#                     non_related_fields: list[str] = [
#                         field_name
#                         for field_name in config.list_schema.model_fields.keys()
#                         if field_name
#                         not in related_models + many_to_many_models + property_fields
#                     ]
#
#                     all_fields: list[str] = non_related_fields + related_fields
#
#                     qs = qs.select_related(*related_models).prefetch_related(
#                         *many_to_many_models,
#                     )  # To avoid N+1 queries
#                     qs = qs.values(*all_fields)
#                     return qs
#
#         # Add (overwrite if necessary) all mro attributes to the CrudlBase class
#         # This allows the CrudlBase class to inherit all attributes from
#         # parent class of the `Crudl` class.
#         for base in bases:
#             for attr_name, attr_value in base.__dict__.items():
#                 if not attr_name.startswith("__"):
#                     setattr(CrudlBase, attr_name, attr_value)
#
#         # Add (overwrite if necessary) all dct attributes to the CrudlBase class
#         for attr_name, attr_value in dct.items():
#             if not attr_name.startswith("__"):
#                 setattr(CrudlBase, attr_name, attr_value)
#
#         for attr_name, attr_value in CrudlBase.__dict__.items():
#             if not attr_name.startswith("__"):
#                 dct[attr_name] = attr_value
#
#         # Add ControllerBase as a base class
#         bases = (ControllerBase,)
#
#         return super().__new__(cls, name, bases, dct)
#
#     @classmethod
#     def _create_schema_extra(
#         cls,
#         get_one_operation_id: str,
#         update_operation_id: str,
#         partial_update_operation_id: str,
#         delete_operation_id: str,
#         create_response_name: str,
#         resource_name: str,
#     ) -> JSON:  # pyre-ignore[11]
#         """Create the OpenAPI extra for the create operation."""
#         res_body_id = "$response.body#/id"
#         return {
#             "responses": {
#                 201: {
#                     "description": "Created",
#                     "content": {
#                         "application/json": {
#                             "schema": {
#                                 "$ref": f"#/components/schemas/{create_response_name}",
#                             },
#                         },
#                     },
#                     "links": {
#                         "UpdateById": {
#                             "operationId": update_operation_id,
#                             "parameters": {"id": res_body_id},
#                             "description": f"Update {resource_name} by id",
#                         },
#                         "DeleteById": {
#                             "operationId": delete_operation_id,
#                             "parameters": {"id": res_body_id},
#                             "description": f"Delete {resource_name} by id",
#                         },
#                         "GetById": {
#                             "operationId": get_one_operation_id,
#                             "parameters": {"id": res_body_id},
#                             "description": f"Get {resource_name} by id",
#                         },
#                         "PatchById": {
#                             "operationId": partial_update_operation_id,
#                             "parameters": {"id": res_body_id},
#                             "description": f"Patch {resource_name} by id",
#                         },
#                     },
#                 },
#                 **not_authorized_openapi_extra,
#                 **throttle_openapi_extra,
#             },
#         }
