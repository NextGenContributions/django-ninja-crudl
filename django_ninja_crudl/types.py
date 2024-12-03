"""Shared types for the CRUDL classes."""

from dataclasses import dataclass
from typing import Any, Literal

from django.db.models import Model
from django.http import HttpRequest
from pydantic import BaseModel

PathArgs = dict[str, Any]
ObjectlessActions = Literal["create", "list"]
WithObjectActions = Literal["get_one", "put", "patch", "delete"]


@dataclass
class RequestDetails[TDjangoModel: Model]:
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
    action: ObjectlessActions | WithObjectActions
    schema: type[BaseModel] | None = None
    path_args: PathArgs | None = None
    payload: BaseModel | None = None
    model_class: type[TDjangoModel] | None = None
    object: TDjangoModel | None = None
    related_model_class: type[Model] | None = None
    related_object: Model | None = None
