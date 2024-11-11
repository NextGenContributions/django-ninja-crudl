"""This module contains OpenAPI extras for errors."""

from ninja_extra import status

not_authorized_openapi_extra = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "headers": {
            "WWW-Authenticate": {
                "description": "The authentication method that should be used to gain access.",
                "schema": {
                    "type": "string",
                },
            },
        },
    },
}

throttle_openapi_extra = {
    status.HTTP_429_TOO_MANY_REQUESTS: {
        "description": "Too many requests",
        "headers": {
            "Retry-After": {
                "description": "The number of seconds to wait before making a new request.",
                "schema": {
                    "type": "integer",
                    "minimum": 0,
                },
            },
        },
    },
}
