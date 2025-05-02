"""Test validate OpenAPI specs."""

import json
from typing import TYPE_CHECKING

from ninja.responses import NinjaJSONEncoder
from openapi_spec_validator import validate

from tests.test_django.urls import api

if TYPE_CHECKING:
    from ninja.openapi.schema import OpenAPISchema


def test_validate_openapi_specs() -> None:
    """Test that the OpenAPI specs are valid."""
    schema: OpenAPISchema = api.get_openapi_schema()
    schema_json = json.dumps(schema, cls=NinjaJSONEncoder)
    schema_dict = json.loads(schema_json)  # pyright: ignore [reportAny]
    validate(schema_dict)  # pyright: ignore [reportAny]
