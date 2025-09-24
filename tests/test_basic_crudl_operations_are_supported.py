"""Test the API endpoints."""

from unittest.mock import patch

import pytest
from django.test import Client
from ninja_extra import status

from tests.test_django.app.models import Publisher


@pytest.mark.django_db
def test_publisher_save_signals_are_called_only_once(client: Client) -> None:
    """Test that the save signals are called only once during POST request."""
    with (
        patch("tests.test_django.app.signals.pre_save_publisher_mock") as pre_save,
        patch("tests.test_django.app.signals.post_save_publisher_mock") as post_save,
    ):
        _ = client.post(
            "/api/publishers",
            content_type="application/json",
            data={
                "name": "Some publisher",
                "address": "Some address",
            },
        )
        pre_save.assert_called_once()
        post_save.assert_called_once()


@pytest.mark.django_db
def test_create_resource_with_post_works(client: Client) -> None:
    """Test creating a resource with POST request."""
    response = client.post(
        "/api/publishers",
        content_type="application/json",
        data={
            "name": "Some publisher",
            "address": "Some address",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
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
    assert response.status_code == status.HTTP_200_OK, response.json()
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
    response = client.get("/api/publishers")
    assert response.status_code == status.HTTP_200_OK, response.json()
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
    assert response.status_code == status.HTTP_200_OK, response.json()
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
    assert response.status_code == status.HTTP_200_OK, response.json()
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
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    with pytest.raises(Publisher.DoesNotExist):
        p.refresh_from_db()


@pytest.mark.django_db
def test_create_property_with_post_works(client: Client) -> None:
    """Test creating a resource that has a property with POST request."""
    response = client.post(
        f"/api/publishers",
        content_type="application/json",
        data={
            "name": "Some publisher",
            "address": "Some address",
            "website": "https://some-publisher.com",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    p = Publisher.objects.get(id=response.json()["id"])
    assert p.name == "Some publisher"
    assert p.address == "Some address"
    assert str(p.website) == "https://some-publisher.com/"


@pytest.mark.django_db
def test_update_property_with_put_patch_works(client: Client) -> None:
    """Test updating a resource that has a property with PUT/PATCH request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    # PATCH
    response = client.patch(
        f"/api/publishers/{p.id}",
        content_type="application/json",
        data={
            "website": "https://some-publisher.com",
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    p.refresh_from_db()
    assert p.name == "Some publisher"
    assert p.address == "Some address"
    assert str(p.website) == "https://some-publisher.com/"

    # PUT
    response = client.put(
        f"/api/publishers/{p.id}",
        content_type="application/json",
        data={
            "name": "Updated publisher",
            "address": "Updated address",
            "website": "https://updated-publisher.com",
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    p.refresh_from_db()
    assert p.name == "Updated publisher"
    assert p.address == "Updated address"
    assert str(p.website) == "https://updated-publisher.com/"
