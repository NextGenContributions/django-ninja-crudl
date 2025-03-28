import django.core.exceptions as dj_exc

from django_ninja_crudl.types import DictStrAny


def transform_django_validation_error(message_dict: DictStrAny) -> list[DictStrAny]:
    """Handle Django validation errors."""
    result: list[DictStrAny] = []

    for field, error_messages in message_dict.items():
        for message in error_messages:
            result.append(
                {
                    "loc": ["body", "payload", field],
                    "msg": message,
                    "type": "django_validation",
                }
            )

    return result


def get_exception_details(exc: Exception | None) -> str | list[DictStrAny] | None:
    """Transform the exception response into a format similar to django-ninja."""
    if isinstance(exc, dj_exc.ValidationError):
        return transform_django_validation_error(exc.message_dict)

    # Generic error response
    if exc is not None:
        return str(exc)

    return None
