"""Test API permissions."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models
from tests.test_django.urls import ADMIN_USER, RESTRICTED_USER, STANDARD_USER


@pytest.mark.django_db
def test_partial_update_resource_while_unauthenticated_should_fail(
    client: Client,
) -> None:
    """Test partially updating a resource with PATCH request."""
    author = models.Author.objects.create(
        name="Patch Author", birth_date=datetime.date(1990, 1, 1)
    )
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_partial_update_resource_with_unpermitted_user_should_fail(
    client: Client,
) -> None:
    """Test partially updating a resource with PATCH request."""
    author = models.Author.objects.create(
        name="Patch Author", birth_date=datetime.date(1990, 1, 1)
    )
    u = User.objects.create_user(RESTRICTED_USER)
    client.force_login(u)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_partial_update_permitted_resource_with_permitted_user_should_succeed(
    client: Client,
) -> None:
    """Test updating a resource with PUT request."""
    u = User.objects.create_user(STANDARD_USER)
    author = models.Author.objects.create(
        name="Update Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=u,
    )

    client.force_login(u)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.name == "Patched Author"


@pytest.mark.django_db
def test_partial_update_unpermitted_resource_with_permitted_user_should_fail(
    client: Client,
) -> None:
    """Test updating a resource with PUT request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    # Resources created by admin
    author = models.Author.objects.create(
        name="Update Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=admin,
    )

    client.force_login(std_usr)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Patched Author",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


@pytest.mark.django_db
def test_partial_update_permitted_resource_with_permitted_simple_related_resource_should_succeed(
    client: Client,
) -> None:
    """Test updating a resource with PUT request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    author = models.Author.objects.create(
        name="Update Author",
        birth_date=datetime.date(1990, 1, 1),
    )

    client.force_login(admin)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "user": std_usr.id,  # Referencing permitted OneToOneField related resource
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.user_id == std_usr.id


@pytest.mark.django_db
def test_partial_update_permitted_resource_with_permitted_complex_related_resource_should_succeed(
    client: Client,
) -> None:
    """Test updating a resource with PUT request."""
    std_usr = User.objects.create_user(STANDARD_USER)

    # Resources created by the user themselves
    author = models.Author.objects.create(
        name="Update Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=std_usr,
    )
    publisher: models.Publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
        created_by=std_usr,
    )
    book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publisher=publisher,
        publication_date="2021-01-01",
        created_by=std_usr,
    )

    client.force_login(std_usr)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "books": [
                book.id  # Referencing permitted ManyToManyRel related resource
            ],
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.books.count() == 1
    assert (b := author.books.first()) is not None and b.id == book.id


@pytest.mark.django_db
def test_partial_update_permitted_resource_with_unpermitted_simple_related_resource_should_fail(
    client: Client,
) -> None:
    """Test updating a resource with PUT request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    # Resources created by the user themselves
    author = models.Author.objects.create(
        name="Update Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=std_usr,
    )

    client.force_login(std_usr)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "user": admin.id,  # Referencing unpermitted OneToOneField related resource
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


@pytest.mark.django_db
def test_partial_update_permitted_resource_with_unpermitted_complex_related_resource_should_fail(
    client: Client,
) -> None:
    """Test updating a resource with PUT request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    # Resources created by the user themselves
    author = models.Author.objects.create(
        name="Update Author",
        birth_date=datetime.date(1990, 1, 1),
        created_by=std_usr,
    )

    # Resources created by admin
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

    client.force_login(std_usr)
    response = client.patch(
        f"/api/gated-authors/{author.id}",
        content_type="application/json",
        data={
            "books": [
                book.id  # Referencing unpermitted ManyToManyRel related resource
            ],
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()
