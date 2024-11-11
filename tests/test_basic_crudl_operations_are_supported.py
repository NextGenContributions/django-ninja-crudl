"""Test the API endpoints."""

import pytest
from django.test import Client
from ninja_extra import status

from tests.test_django.app.models import Publisher


@pytest.mark.django_db
def test_create_resource_with_post_works(client: Client) -> None:
    """Test creating a resource with POST request."""
    response = client.post(
        "/api/publishers/",
        content_type="application/json",
        data={
            "name": "Some publisher",
            "address": "Some address",
        },
    )
    print(response.content)
    assert response.status_code == status.HTTP_201_CREATED
    p = Publisher.objects.get(id=response.json()["id"])
    assert p.name == "Some publisher"
    assert p.address == "Some address"


@pytest.mark.django_db
def test_get_resource_works(client: Client) -> None:
    """Test getting a resource by id with GET request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    response = client.get(f"/api/publishers/{p.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": p.id,
        "name": "Some publisher",
        "address": "Some address",
    }


@pytest.mark.django_db
def test_list_resources_works(client: Client) -> None:
    """Test listing resources with GET request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    response = client.get("/api/publishers/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": p.id,
            "name": "Some publisher",
            "address": "Some address",
        },
    ]


@pytest.mark.django_db
def test_update_resource_with_put_works(client: Client) -> None:
    """Test updating a resource with PUT request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    response = client.put(
        f"/api/publishers/{p.id}",
        content_type="application/json",
        data={
            "name": "Updated publisher",
            "address": "Updated address",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    p.refresh_from_db()
    assert p.name == "Updated publisher"
    assert p.address == "Updated address"


@pytest.mark.django_db
def test_update_resource_with_patch_works(client: Client) -> None:
    """Test updating a resource with PATCH request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    response = client.patch(
        f"/api/publishers/{p.id}",
        content_type="application/json",
        data={
            "name": "Updated publisher",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    p.refresh_from_db()
    assert p.name == "Updated publisher"
    assert p.address == "Some address"


@pytest.mark.django_db
def test_delete_resource_works(client: Client) -> None:
    """Test deleting a resource with DELETE request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    response = client.delete(f"/api/publishers/{p.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    with pytest.raises(Publisher.DoesNotExist):
        p.refresh_from_db()
