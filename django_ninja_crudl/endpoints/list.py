"""CRUDL API base class."""

import logging
from abc import ABC
from typing import TYPE_CHECKING, Literal, Unpack

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from ninja_extra import http_get, status

from django_ninja_crudl import CrudlConfig
from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error422UnprocessableEntitySchema,
    Error503ServiceUnavailableSchema,
    ErrorSchema,
)
from django_ninja_crudl.types import (
    RequestDetails,
    RequestParams,
    TDjangoModel,
)
from django_ninja_crudl.utils import (
    replace_path_args_annotation,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


def get_get_many_endpoint(config: CrudlConfig[TDjangoModel]) -> type | None:
    """Create the get_many endpoint class for the CRUDL operations."""
    if not config.list_schema:
        return None

    list_schema: type[BaseModel] = config.list_schema

    class GetManyEndpoint(CrudlBaseMethodsMixin[TDjangoModel], ABC):  # pyright: ignore [reportGeneralTypeIssues]
        """GetMany endpoint for CRUDL operations."""

        @http_get(
            path=config.list_path,
            response={
                status.HTTP_200_OK: list[list_schema],  # type: ignore[valid-type]
                status.HTTP_401_UNAUTHORIZED: Error401UnauthorizedSchema,
                status.HTTP_403_FORBIDDEN: Error403ForbiddenSchema,
                status.HTTP_422_UNPROCESSABLE_ENTITY: Error422UnprocessableEntitySchema,
                status.HTTP_503_SERVICE_UNAVAILABLE: Error503ServiceUnavailableSchema,
            },
            operation_id=config.list_operation_id,
            url_name=config.list_operation_id,
            # openapi_extra=config.openapi_extra,
        )
        @replace_path_args_annotation(config.list_path, config.model)
        def get_many(  # noqa: WPS210
            self,
            request: HttpRequest,
            response: HttpResponse,
            **kwargs: Unpack[RequestParams],
        ) -> (
            tuple[Literal[401, 403], ErrorSchema] | QuerySet[TDjangoModel, TDjangoModel]
        ):
            """List all objects."""
            request_details = RequestDetails[TDjangoModel](
                action="list",
                request=request,
                path_args=self._get_path_args(kwargs),
                model_class=config.model,
            )

            if not self.is_authenticated(request_details):
                return self.get_401_error(request)
            if not self.has_permission(request_details):
                return self.get_403_error(request)

            qs = (
                self.get_pre_filtered_queryset(config.model, request_details.path_args)
                .filter(self.get_base_filter(request_details))
                .filter(self.get_filter_for_list(request_details))
            )

            # Return the total count of objects in the response headers
            response["x-total-count"] = qs.count()
            # TODO(phuongfi91): support pagination
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/34
            # TODO(phuongfi91): optimize the query
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            return qs

            # The following code are extremely janky and won't be used for now
            ############################################################
            # # Extract the related models from the ListSchema fields
            # related_models: list[str] = []
            # many_to_many_models: list[str] = []
            # related_fields: list[str] = []
            # property_fields: list[str] = []
            # m2m_fields: list[str] = []
            #
            # for field_name in list_schema.model_fields:
            #     attr = getattr(config.model, field_name, None)  # noqa: WPS220
            #
            #     # Skip @property methods here
            #     if attr and isinstance(attr, property):
            #         property_fields.append(field_name)  # noqa: WPS220
            #         # TODO(jhassine): Implement a way to avoid N+1 queries when using @property methods
            #         logger.debug(  # noqa: WPS220
            #             "Detected use of @property method %s of the model %s in"
            #             " list_fields definition which"
            #             " may cause N+1 queries and cause performance degradation.",
            #             field_name,
            #             config.model,
            #         )
            #         continue
            #         # return qs  # noqa: WPS220
            #
            #     django_field = get_model_field(config.model, field_name)
            #     if type(django_field) in {
            #         ForeignKey,
            #         OneToOneField,
            #         OneToOneRel,
            #     }:
            #         related_models.append(field_name)  # noqa: WPS220
            #         related_fields.extend(  # noqa: WPS220
            #             set(
            #                 [f"{field_name}__pk"]
            #                 + get_pydantic_fields(
            #                     list_schema,
            #                     field_name,
            #                 )
            #             ),
            #         )
            #
            #     elif type(django_field) in {
            #         models.ManyToManyField,
            #         models.ManyToManyRel,
            #         models.ManyToOneRel,
            #     }:
            #         many_to_many_models.append(field_name)  # noqa: WPS220
            #         m2m_fields.extend(  # noqa: WPS220
            #             get_pydantic_fields(
            #                 list_schema,
            #                 field_name,
            #             ),
            #         )
            #
            # non_related_fields: list[str] = [
            #     field_name
            #     for field_name in list_schema.model_fields.keys()
            #     if field_name
            #     not in related_models + many_to_many_models + property_fields
            # ]
            #
            # # TODO(phuongfi91): support returning property fields
            # #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            # all_fields: list[str] = non_related_fields + related_fields
            #
            # qs = qs.select_related(*related_models).prefetch_related(
            #     *many_to_many_models,
            # )  # To avoid N+1 queries
            # qs = qs.values(*all_fields)
            #
            # # TODO(phuongfi91): find alternative to this janky solution
            # #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            # # add m2m fields (with supported structure) to the response
            # l = cast("list[dict[str, Any]]", list(qs))  # pyright: ignore [reportExplicitAny]
            # for i in l:
            #     for r in related_models:
            #         if i[f"{r}__pk"] is None:
            #             # remove all related fields if the related model is doesn't exist
            #             keys_to_remove = [f for f in i.keys() if f.startswith(f"{r}__")]
            #             for k in keys_to_remove:
            #                 _ = i.pop(k, None)  # pyright: ignore [reportAny]
            #         elif f"{r}__pk" not in get_pydantic_fields(list_schema, r):
            #             # only remove related field pk if it wasn't explicitly requested in the schema
            #             _ = i.pop(f"{r}__pk", None)  # pyright: ignore [reportAny]
            #
            #     for m in many_to_many_models:
            #         from django.db.models import F
            #
            #         relevant_m2m_fields = set(
            #             [f"{m}__pk"]
            #             + list(filter(lambda x: x.startswith(m), m2m_fields))
            #         )
            #         m2m_values = list(
            #             config.model._default_manager.filter(id=i["id"])
            #             .values(*relevant_m2m_fields)
            #             .values(
            #                 **{
            #                     f.removeprefix(f"{m}__"): F(f)
            #                     for f in relevant_m2m_fields
            #                 }
            #             )
            #         )
            #
            #         # only keep m2m values that are not None
            #         m2m_values = [v for v in m2m_values if v["pk"] is not None]
            #
            #         # remove m2m field pk if it wasn't explicitly requested in the schema
            #         if f"{m}__pk" not in get_pydantic_fields(list_schema, m):
            #             for v in m2m_values:
            #                 _ = v.pop("pk", None)  # pyright: ignore [reportAny]
            #
            #         i[m] = m2m_values
            #
            # return l

    return GetManyEndpoint
