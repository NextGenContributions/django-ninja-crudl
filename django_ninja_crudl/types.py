"""Shared types for the CRUDL classes."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypedDict, TypeVar

from beartype import beartype
from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from django.http import HttpRequest
from pydantic import BaseModel

TDjangoModel = TypeVar("TDjangoModel", bound=Model)

# TODO(phuongfi91): Should this be used somewhere?
#  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)

type PathArgs = dict[str, Any]  # pyright: ignore[reportExplicitAny]
type ObjectlessActions = Literal["create", "list"]
type WithObjectActions = Literal["get_one", "put", "patch", "delete"]
type JSON = dict[str | int, "JSON"] | list["JSON"] | str | int | float | bool | None
type DjangoFieldType = tuple[str, Any]  # pyright: ignore[reportExplicitAny]
type DictStrAny = dict[str, Any]  # pyright: ignore[reportExplicitAny]


class RequestParams(TypedDict, total=False):
    """The URL path arguments of request."""

    path_args: BaseModel


@beartype
@dataclass
class RequestDetails(Generic[TDjangoModel]):  # pylint: disable=too-many-instance-attributes
    """Details about the request.

    Used to pass information to the CRUDL methods.

    The RequestDetails object contains as much information as possible about the request that is available at the time of the call.

    For has_permission() methods, the RequestDetails object contains the following attributes:
        request: The Django request object.
        action: The action to perform. Is one of the "create", "list", "get_one", "put", "patch", "delete" actions.
        schema: The Pydantic schema to use for the payload.
        path_args: The URL path arguments of the request.
        payload: The payload data.
        model_class: The Django model class to use.

    For has_object_permission() methods, the RequestDetails object contains additional attributes:
        object: The Django model object to use.

    For has_related_object_permission() methods, the RequestDetails object contains additional attributes:
        related_model_class: The related Django model class to use.
        related_object: The related Django model object to use.

    Attributes:
        request: The Django request object.
        action: The action to perform. Is one of the "create", "list", "get_one", "put", "patch", "delete" actions.
        schema: The Pydantic schema to use for the payload.
        path_args: The URL path arguments of the request.
        payload: The payload data.
        model_class: The Django model class to use.
        object: The Django model object to use.
        related_model_class: The related Django model class to use.
        related_object: The related Django model object to use.

    """

    request: HttpRequest
    """The Django HTTP request object."""

    action: ObjectlessActions | WithObjectActions
    """The action to perform. Is one of the "create", "list", "get_one", "put", "patch", "delete" actions."""

    schema: type[BaseModel] | None = None
    """The Pydantic schema to use for the payload."""

    path_args: PathArgs | None = None
    """The URL path arguments of the request."""

    payload: BaseModel | None = None
    """The payload data from the request."""

    model_class: type[TDjangoModel] | None = None
    """The Django model class to use."""

    object: TDjangoModel | None = None
    """The Django model object to use."""

    related_model_class: type[TDjangoModel] | None = None
    """The related Django model class to use."""

    related_object: TDjangoModel | None = None
    """The related Django model object to use."""
