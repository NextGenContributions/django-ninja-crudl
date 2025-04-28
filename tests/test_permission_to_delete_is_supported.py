"""Test API permissions."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models
from tests.test_django.urls import ADMIN_USER, RESTRICTED_USER, STANDARD_USER


@pytest.mark.django_db
def test_delete_resource_while_unauthenticated_should_fail(client: Client) -> None:
    """Test deleting a resource with DELETE request."""
    author = models.Author.objects.create(
        name="Delete Author", birth_date=datetime.date(1990, 1, 1)
    )
    response = client.delete(f"/api/gated-authors/{author.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_delete_resource_with_unpermitted_user_should_fail(client: Client) -> None:
    """Test deleting a resource with DELETE request."""
    author = models.Author.objects.create(
        name="Delete Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(RESTRICTED_USER)
    client.force_login(u)
    response = client.delete(f"/api/gated-authors/{author.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_delete_permitted_resource_with_permitted_user_should_succeed(
    client: Client,
) -> None:
    """Test deleting a resource with DELETE request."""
    std_usr = User.objects.create_user(STANDARD_USER)

    # Created by the user themselves
    author = models.Author.objects.create(
        name="Delete Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=std_usr,
    )

    client.force_login(std_usr)
    response = client.delete(f"/api/gated-authors/{author.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not models.Author.objects.filter(id=author.id).exists()


@pytest.mark.django_db
def test_delete_unpermitted_resource_with_permitted_user_should_fail(
    client: Client,
) -> None:
    """Test deleting a resource with DELETE request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    # Created by admin
    author = models.Author.objects.create(
        name="Delete Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=admin,
    )

    client.force_login(std_usr)
    response = client.delete(f"/api/gated-authors/{author.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert models.Author.objects.filter(id=author.id).exists()


@pytest.mark.django_db
def test_delete_permitted_resource_with_unpermitted_related_resource_should_succeed(
    client: Client,
) -> None:
    # TODO(phuongfi91): What about deleting with cascading against unpermitted related resources?
    """Test deleting a resource with DELETE request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    # Created by admin
    publisher: models.Publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
        created_by=admin,
    )
    book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publisher=publisher,
        publication_date="2021-01-01",
        created_by=admin,
    )

    # Created by the user themselves
    author = models.Author.objects.create(
        name="Delete Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=std_usr,
    )
    author.books.set([book])  # type: ignore[attr-defined]

    client.force_login(std_usr)
    response = client.delete(f"/api/gated-authors/{author.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not models.Author.objects.filter(id=author.id).exists()
    assert models.Book.objects.filter(id=book.id).exists()
