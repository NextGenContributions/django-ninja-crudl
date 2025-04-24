"""Test API permissions."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client
from ninja_extra import status

from tests.test_django.app.models import Author

AUTHORIZED_USER_NAME = "john_doe"
UNAUTHORIZED_USER_NAME = "jane_doe"


@pytest.mark.django_db
def test_create_resource_without_logging_in_should_fail(client: Client) -> None:
    """Test creating a resource with POST request."""
    response = client.post(
        "/api/authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_create_resource_with_unauthorized_user_should_fail(client: Client) -> None:
    """Test creating a resource with POST request."""
    u = User.objects.create_user(UNAUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.post(
        "/api/authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_create_resource_with_authorized_user_should_succeed(client: Client) -> None:
    """Test creating a resource with POST request."""
    u = User.objects.create_user(AUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.post(
        "/api/authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    p = Author.objects.get(id=response.json()["id"])
    assert p.name == "Some author"
    assert p.birth_date == datetime.date(1990, 1, 1)


@pytest.mark.django_db
def test_list_resources_without_logging_in_should_fail(client: Client) -> None:
    """Test listing resources with GET request."""
    response = client.get("/api/authors")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_list_resources_with_unauthorized_user_should_fail(client: Client) -> None:
    """Test listing resources with GET request."""
    u = User.objects.create_user(UNAUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.get("/api/authors")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_list_resources_with_authorized_user_should_succeed(client: Client) -> None:
    """Test listing resources with GET request."""
    Author.objects.create(name="Test Author 1", birth_date=datetime.date(1990, 1, 1))
    Author.objects.create(name="Test Author 2", birth_date=datetime.date(1985, 5, 5))

    u = User.objects.create_user(AUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.get("/api/authors")

    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] in ["Test Author 1", "Test Author 2"]


@pytest.mark.django_db
def test_get_one_resource_without_logging_in_should_fail(client: Client) -> None:
    """Test retrieving a single resource with GET request."""
    author = Author.objects.create(
        name="Get Author", birth_date=datetime.date(1990, 1, 1)
    )
    response = client.get(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_get_one_resource_with_unauthorized_user_should_fail(client: Client) -> None:
    """Test retrieving a single resource with GET request."""
    author = Author.objects.create(
        name="Get Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(UNAUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.get(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_get_one_resource_with_authorized_user_should_succeed(client: Client) -> None:
    """Test retrieving a single resource with GET request."""
    author = Author.objects.create(
        name="Get Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(AUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.get(f"/api/authors/{author.id}")

    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert data["name"] == "Get Author"
    assert data["birth_date"] == "1990-01-01"


@pytest.mark.django_db
def test_update_resource_without_logging_in_should_fail(client: Client) -> None:
    """Test updating a resource with PUT request."""
    author = Author.objects.create(
        name="Update Author", birth_date=datetime.date(1990, 1, 1)
    )
    response = client.put(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Updated Author",
            "birth_date": "1995-05-05",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_update_resource_with_unauthorized_user_should_fail(client: Client) -> None:
    """Test updating a resource with PUT request."""
    author = Author.objects.create(
        name="Update Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(UNAUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.put(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Updated Author",
            "birth_date": "1995-05-05",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_update_resource_with_authorized_user_should_succeed(client: Client) -> None:
    """Test updating a resource with PUT request."""
    author = Author.objects.create(
        name="Update Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(AUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.put(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Updated Author",
            "birth_date": "1995-05-05",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.name == "Updated Author"
    assert author.birth_date == datetime.date(1995, 5, 5)


@pytest.mark.django_db
def test_update_partial_resource_without_logging_in_should_fail(client: Client) -> None:
    """Test partially updating a resource with PATCH request."""
    author = Author.objects.create(
        name="Patch Author", birth_date=datetime.date(1990, 1, 1)
    )
    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_update_partial_resource_with_unauthorized_user_should_fail(
    client: Client,
) -> None:
    """Test partially updating a resource with PATCH request."""
    author = Author.objects.create(
        name="Patch Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(UNAUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_update_partial_resource_with_authorized_user_should_succeed(
    client: Client,
) -> None:
    """Test partially updating a resource with PATCH request."""
    author = Author.objects.create(
        name="Patch Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(AUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.name == "Patched Author"
    assert author.birth_date == datetime.date(1990, 1, 1)  # Unchanged


@pytest.mark.django_db
def test_delete_resource_without_logging_in_should_fail(client: Client) -> None:
    """Test deleting a resource with DELETE request."""
    author = Author.objects.create(
        name="Delete Author", birth_date=datetime.date(1990, 1, 1)
    )
    response = client.delete(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_delete_resource_with_unauthorized_user_should_fail(client: Client) -> None:
    """Test deleting a resource with DELETE request."""
    author = Author.objects.create(
        name="Delete Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(UNAUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.delete(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_delete_resource_with_authorized_user_should_succeed(client: Client) -> None:
    """Test deleting a resource with DELETE request."""
    author = Author.objects.create(
        name="Delete Author", birth_date=datetime.date(1990, 1, 1)
    )
    author_id = author.id
    u = User.objects.create_user(AUTHORIZED_USER_NAME)
    client.force_login(u)
    response = client.delete(f"/api/authors/{author.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Author.objects.filter(id=author_id).exists()
