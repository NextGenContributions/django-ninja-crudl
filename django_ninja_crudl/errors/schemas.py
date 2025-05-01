"""Error response schemas for the CRUDL API."""

from typing import ClassVar, Literal

from django.utils.translation import gettext as _
from pydantic import BaseModel, ConfigDict

from django_ninja_crudl.types import DictStrAny

# TODO(phuongfi91): Tests error schemas


class ErrorSchema(BaseModel):
    """The default error schema."""

    model_config: ClassVar[ConfigDict] = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }

    success: Literal[False] = False
    code: str
    message: str = ""
    user_friendly_message: str = ""
    request_id: str = ""
    details: str | list[DictStrAny] | None = None


class Error401UnauthorizedSchema(ErrorSchema):
    """The default unauthorized schema."""

    code: str = "Unauthorized"
    message: str = (
        "Authentication credentials were not provided or they were incorrect."
    )
    user_friendly_message: str = _("Please log in to access this resource.")


class Error403ForbiddenSchema(ErrorSchema):
    """The default forbidden schema."""

    code: str = "Forbidden"
    message: str = "You do not have permission to perform this action on this endpoint."
    user_friendly_message: str = _("You do not have permission to perform this action.")


class Error404NotFoundSchema(ErrorSchema):
    """The default resource not found schema."""

    code: str = "ResourceNotFound"
    message: str = (
        "The requested resource was not found or you do not have permission "
        "to access it."
    )
    user_friendly_message: str = _(
        "The requested resource was not found or you do not have permission to "
        "access it."
    )


class Error409ConflictSchema(ErrorSchema):
    """The default conflict schema."""

    code: str = "Conflict"
    message: str = (
        "The request could not be completed due to a conflict with the "
        "current state of the resource."
    )
    user_friendly_message: str = _(
        "The request could not be completed due to a conflict."
    )


class Error422UnprocessableEntitySchema(ErrorSchema):
    """The default unprocessable entity schema."""

    code: str = "UnprocessableEntity"
    message: str = "The request could not be processed due to semantic errors."
    user_friendly_message: str = _(
        "The request could not be processed due to semantic errors."
    )


class Error429TooManyRequestSchema(ErrorSchema):
    """The default too many requests schema."""

    code: str = "TooManyRequests"
    message: str = "You have exceeded the rate limit for this endpoint."
    user_friendly_message: str = _(
        "You have exceeded the rate limit. You can try again in a few minutes."
    )


class Error503ServiceUnavailableSchema(ErrorSchema):
    """The default service unavailable schema."""

    code: str = "ServiceUnavailable"
    message: str = (
        "The server is currently unable to handle the request due to a "
        "temporary overloading or maintenance of the server."
    )
    user_friendly_message: str = _(
        "The server is currently unavailable. Please try again later."
    )
