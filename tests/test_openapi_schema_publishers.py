"""Test Publishers Id OpenAPI schema."""
# pylint: disable=redefined-outer-name

import json
from typing import Any

import pytest
from ninja.openapi.schema import OpenAPISchema

from tests.utils import IntegerKeyJSONDecoder


@pytest.fixture
def openapi_schema() -> OpenAPISchema:
    """Get the OpenAPI schema."""
    # return client.get("/api/openapi.json").json()
    from tests.test_django.urls import api

    return api.get_openapi_schema()


@pytest.fixture
def api_publishers() -> dict[str, Any]:  # pyright: ignore [reportExplicitAny]
    """Load a JSON fixture from the given file path."""
    with open("./fixtures/api_publishers.json") as file:
        return json.load(file, cls=IntegerKeyJSONDecoder)  # type: ignore[no-any-return]


def test_openapi_schema_publishers_id(
    openapi_schema: OpenAPISchema,
    api_publishers: dict[str, Any],  # pyright: ignore [reportExplicitAny]
) -> None:
    """Test that the publishers/{id} endpoint has a 200 response."""
    assert openapi_schema["paths"]["/api/publishers"] == api_publishers
