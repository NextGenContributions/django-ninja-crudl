"""Shared types for the CRUDL classes."""

from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar

from beartype import beartype
from django.db.models import Model
from django.http import HttpRequest
from pydantic import BaseModel

TDjangoModel = TypeVar("TDjangoModel", bound=Model)
TDjangoModel_co = TypeVar("TDjangoModel_co", bound=Model, covariant=True)


type PathArgs = dict[str, Any]  # pyright: ignore[reportExplicitAny]
type ObjectlessActions = Literal["create", "list"]
type WithObjectActions = Literal["get_one", "put", "patch", "delete"]

type JSON = (  # pyre-ignore[11]
    None | bool | int | float | str | list["JSON"] | dict[str | int, "JSON"]  # noqa: WPS221, WPS465
)

type DictStrAny = dict[str, Any]  # pyright: ignore[reportExplicitAny]


@beartype
@dataclass
class RequestDetails(Generic[TDjangoModel_co]):
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

    model_class: type[TDjangoModel_co] | None = None
    """The Django model class to use."""

    object: TDjangoModel_co | None = None
    """The Django model object to use."""

    related_model_class: type[Model] | None = None
    """The related Django model class to use."""

    related_object: Model | None = None
    """The related Django model object to use."""
