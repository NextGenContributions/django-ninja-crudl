from typing import Literal

from pydantic import BaseModel


class ErrorSchema(BaseModel):
    """The default error schema."""

    success: Literal[False] = False
    code: str
    message: str
    request_id: str = ""


class ResourceNotFound404Schema(ErrorSchema):
    """The default resource not found schema."""

    code: str = "ResourceNotFound"


class Conflict409Schema(ErrorSchema):
    """The default conflict schema."""

    code: str = "Conflict"
