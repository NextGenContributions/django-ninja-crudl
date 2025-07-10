"""Test Publishers Id OpenAPI schema."""
# pylint: disable=redefined-outer-name

import json
from pathlib import Path
from typing import Any

import pytest
from ninja.openapi.schema import OpenAPISchema

from tests.utils import IntegerKeyJSONDecoder, normalize_http_status_descriptions


@pytest.fixture
def openapi_schema() -> OpenAPISchema:
    """Get the OpenAPI schema."""
    from tests.test_django.urls import api

    return api.get_openapi_schema()


@pytest.fixture
def api_publishers() -> dict[str, Any]:  # pyright: ignore [reportExplicitAny]
    """Load a JSON fixture from the given file path."""
    fixture_path = Path(__file__).parent / "fixtures"
    with Path.open(fixture_path / "api_publishers.json") as file:
        data = json.load(file, cls=IntegerKeyJSONDecoder)  # type: ignore[no-any-return]
        return normalize_http_status_descriptions(data)


def test_openapi_schema_publishers_id(
    openapi_schema: OpenAPISchema,
    api_publishers: dict[str, Any],  # pyright: ignore [reportExplicitAny]
) -> None:
    """Test that the publishers/{id} endpoint has a 200 response."""
    # Normalize the actual schema to match the expected Python version
    normalized_schema = normalize_http_status_descriptions(dict(openapi_schema))
    assert normalized_schema["paths"]["/api/publishers"] == api_publishers
