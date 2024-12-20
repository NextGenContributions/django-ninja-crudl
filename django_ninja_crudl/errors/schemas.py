from typing import Literal

from pydantic import BaseModel


class ErrorSchema(BaseModel):
    """The default error schema."""

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

    success: Literal[False] = False
    code: str
    message: str = ""
    user_friendly_message: str = ""
    request_id: str = ""
    debug_details: str | None = None


class Unauthorized401Schema(ErrorSchema):
    """The default unauthorized schema."""

    code: str = "Unauthorized"
    message: str = (
        "Authentication credentials were not provided or they were incorrect."
    )
    user_friendly_message: str = "Please log in to access this resource."


class Forbidden403Schema(ErrorSchema):
    """The default forbidden schema."""

    code: str = "Forbidden"
    message: str = "You do not have permission to perform this action."
    user_friendly_message: str = "You do not have permission to access this resource."


class ResourceNotFound404Schema(ErrorSchema):
    """The default resource not found schema."""

    code: str = "ResourceNotFound"
    message: str = (
        "The requested resource was not found or you do not have permission to access it."
    )
    user_friendly_message: str = (
        "The requested resource was not found or you do not have permission to access it."
    )


class Conflict409Schema(ErrorSchema):
    """The default conflict schema."""

    code: str = "Conflict"
    message: str = (
        "The request could not be completed due to a conflict with the current state of the resource."
    )


class UnprocessableEntity422Schema(ErrorSchema):
    """The default unprocessable entity schema."""

    code: str = "UnprocessableEntity"
    message: str = "The request could not be processed due to semantic errors."
    user_friendly_message: str = (
        "The request could not be processed due to semantic errors."
    )


class TooManyRequests429Schema(ErrorSchema):
    """The default too many requests schema."""

    code: str = "TooManyRequests"
    message: str = "You have exceeded the rate limit for this endpoint."
    user_friendly_message: str = (
        "You have exceeded the rate limit. You can try again in a few minutes."
    )


class ServiceUnavailable503Schema(ErrorSchema):
    """The default service unavailable schema."""

    code: str = "ServiceUnavailable"
    message: str = (
        "The server is currently unable to handle the request due to a temporary overloading or maintenance of the server."
    )
    user_friendly_message: str = (
        "The server is currently unavailable. Please try again later."
    )
