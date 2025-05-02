"""Test API calls using the generated OpenAPI schema."""
# pylint: disable=redefined-outer-name

import pytest
from ninja.openapi.schema import OpenAPISchema
from ninja_extra import status


@pytest.fixture
def openapi_schema() -> OpenAPISchema:
    """Get the OpenAPI schema."""
    # return client.get("/api/openapi.json").json()
    from tests.test_django.urls import api

    return api.get_openapi_schema()


def test_create_endpoint_has_201_response(openapi_schema: OpenAPISchema) -> None:
    """Test that the create endpoint has a 201 response."""
    assert openapi_schema["paths"]["/api/publishers"]["post"]["responses"][
        status.HTTP_201_CREATED
    ]


def test_get_endpoint_has_200_response(openapi_schema: OpenAPISchema) -> None:
    """Test that the get endpoint has a 200 response."""
    assert openapi_schema["paths"]["/api/publishers/{id}"]["get"]["responses"][
        status.HTTP_200_OK
    ]


def test_list_endpoint_has_200_response(openapi_schema: OpenAPISchema) -> None:
    """Test that the list endpoint has a 200 response."""
    assert openapi_schema["paths"]["/api/publishers"]["get"]["responses"][
        status.HTTP_200_OK
    ]


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_endpoints_has_right_path_parameters(
    openapi_schema: OpenAPISchema, method: str
) -> None:
    """Test that the get one endpoint has the right path parameters.

    Example structure of the parameter object:
    {
        "description": "ID",
        "in": "path",
        "name": "id",
        "required": True,
        "schema": {
            "description": "ID",
            "maximum": 9223372036854775807,
            "minimum": -9223372036854775808,
            "title": "ID",
            "type": "integer"
        }
    }
    """
    param = openapi_schema["paths"]["/api/publishers/{id}"][method]["parameters"][0]

    assert param["name"] == "id"
    assert param["in"] == "path"
    assert param["required"] is True
    assert param["schema"]["type"] == "integer"
    assert param["schema"]["minimum"] == -9223372036854775808
    assert param["schema"]["maximum"] == 9223372036854775807
    assert param["schema"]["title"] == "ID"


def test_update_endpoint_has_200_response(openapi_schema: OpenAPISchema) -> None:
    """Test that the update endpoint has a 200 response."""
    assert openapi_schema["paths"]["/api/publishers/{id}"]["put"]["responses"][
        status.HTTP_200_OK
    ]


def test_delete_endpoint_has_204_response(openapi_schema: OpenAPISchema) -> None:
    """Test that the delete endpoint has a 204 response."""
    assert openapi_schema["paths"]["/api/publishers/{id}"]["delete"]["responses"][
        status.HTTP_204_NO_CONTENT
    ]


@pytest.mark.skip(reason="WIP")
def test_list_endpoint_has_x_total_count_header(openapi_schema: OpenAPISchema) -> None:
    """Test that the list endpoint has an x-total-count header."""
    assert openapi_schema["paths"]["/api/publishers"]["get"]["responses"][
        status.HTTP_200_OK
    ]["headers"]["x-total-count"]
    assert (
        openapi_schema["paths"]["/api/publishers"]["get"]["responses"][
            status.HTTP_200_OK
        ]["headers"]["x-total-count"]["schema"]["type"]
        == "integer"
    )
    assert (
        openapi_schema["paths"]["/api/publishers/"]["get"]["responses"][
            status.HTTP_200_OK
        ]["headers"]["x-total-count"]["schema"]["minimum"]
        == 0
    )
