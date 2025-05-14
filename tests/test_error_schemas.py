"""Test errors in the API."""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from ninja_extra import status

from django_ninja_crudl.errors.schemas import (
    Error401UnauthorizedSchema,
    Error403ForbiddenSchema,
    Error404NotFoundSchema,
    Error409ConflictSchema,
    Error422UnprocessableEntitySchema,
    Error500InternalServerErrorSchema,
)
from tests.test_django.app import models
from tests.test_django.urls import RESTRICTED_USER


@pytest.mark.django_db
def test_http_401_conforms_with_crudl_error_schema(client: Client) -> None:
    """Test getting a resource with GET request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    response = client.get(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()
    Error401UnauthorizedSchema.model_validate(response.json())


@pytest.mark.django_db
def test_http_403_conforms_with_crudl_error_schema(client: Client) -> None:
    """Test getting a resource with GET request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    u = User.objects.create_user(RESTRICTED_USER)
    client.force_login(u)
    response = client.get(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
    Error403ForbiddenSchema.model_validate(response.json())


@pytest.mark.django_db
def test_http_404_conforms_with_crudl_error_schema(client: Client) -> None:
    """Test getting a resource with GET request."""
    response = client.get(
        "/api/authors/1",
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()
    Error404NotFoundSchema.model_validate(response.json())


@pytest.mark.django_db
def test_http_409_conforms_with_crudl_error_schema(client: Client) -> None:
    """Test creating a resource with POST request."""
    publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    _ = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )

    response = client.post(
        "/api/books",
        content_type="application/json",
        data={
            "title": "Some new book",
            "isbn": "9783161484100",
            "publication_date": "2022-01-01",
            "publisher_id": publisher.id,
            "authors": [author.id],
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT, response.json()
    assert response.json()["detail"][0]["msg"] == "Book with this Isbn already exists."
    Error409ConflictSchema.model_validate(response.json())


@pytest.mark.django_db
def test_http_422_conforms_with_crudl_error_schema(client: Client) -> None:
    """Test updating a resource with POST request."""
    response = client.post(
        "/api/authors",
        content_type="application/json",
        data={
            "bad_name": "Some author",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.json()
    assert response.json()["detail"][0]["msg"] == "Field required"
    assert response.json()["detail"][0]["loc"] == ["body", "payload", "name"]
    Error422UnprocessableEntitySchema.model_validate(response.json())


def get_author_with_mock_internal_server_error(client: Client):  # type: ignore[no-untyped-def]  # noqa: ANN201
    """Get an author with mocked internal server error."""
    with patch(
        "django_ninja_crudl.errors.mixin.ErrorHandlerMixin.get_404_error",
        side_effect=Exception("Internal Server Error"),
    ):
        return client.get(
            "/api/authors/1",
            content_type="application/json",
        )


@override_settings(DEBUG=False)
@pytest.mark.django_db
def test_http_500_with_debug_off_conforms_with_crudl_error_schema(
    client: Client,
) -> None:
    """Test server error when DEBUG is OFF."""
    response = get_author_with_mock_internal_server_error(client)
    assert (
        response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    ), response.json()
    Error500InternalServerErrorSchema.model_validate(response.json())
    assert response.json()["detail"] is None


@override_settings(DEBUG=True)
@pytest.mark.django_db
def test_http_500_with_debug_on_conforms_with_crudl_error_schema(
    client: Client,
) -> None:
    """Test server error when DEBUG is ON."""
    response = get_author_with_mock_internal_server_error(client)
    assert (
        response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    ), response.json()
    Error500InternalServerErrorSchema.model_validate(response.json())
    assert response.json()["detail"] is not None
