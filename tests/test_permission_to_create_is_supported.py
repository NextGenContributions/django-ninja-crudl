"""Test API permissions."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models
from tests.test_django.urls import ADMIN_USER, RESTRICTED_USER, STANDARD_USER


@pytest.mark.django_db
def test_create_resource_while_unauthenticated_should_fail(client: Client) -> None:
    """Test creating a resource with POST request."""
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.json()


@pytest.mark.django_db
def test_create_resource_with_unpermitted_user_should_fail(client: Client) -> None:
    """Test creating a resource with POST request."""
    u = User.objects.create_user(RESTRICTED_USER)
    client.force_login(u)
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


@pytest.mark.django_db
def test_create_resource_with_permitted_user_should_succeed(client: Client) -> None:
    """Test creating a resource with POST request."""
    std_usr = User.objects.create_user(STANDARD_USER)
    client.force_login(std_usr)
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    a = models.Author.objects.get(id=response.json()["id"])
    assert a.name == "Some author"
    assert a.birth_date == datetime.date(1990, 1, 1)


@pytest.mark.django_db
def test_create_resource_with_permitted_simple_related_resource_should_succeed(
    client: Client,
) -> None:
    """Test creating a resource with POST request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    client.force_login(admin)
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "user": std_usr.id,  # Referencing permitted OneToOneField related resource
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    a = models.Author.objects.get(id=response.json()["id"])
    assert a.user_id == std_usr.id
    assert a.name == "Some author"
    assert a.birth_date == datetime.date(1990, 1, 1)


@pytest.mark.django_db
def test_create_resource_with_permitted_complex_related_resource_should_succeed(
    client: Client,
) -> None:
    """Test creating a resource with POST request."""
    std_usr = User.objects.create_user(STANDARD_USER)

    # Resources created by the user themselves
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
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
            "books": [
                book.id  # Referencing permitted ManyToManyRel related resource
            ],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    a = models.Author.objects.get(id=response.json()["id"])
    assert a.name == "Some author"
    assert a.birth_date == datetime.date(1990, 1, 1)
    assert a.books.count() == 1
    assert (b := a.books.first()) is not None and b.id == book.id


@pytest.mark.django_db
def test_create_resource_with_unpermitted_simple_related_resource_should_fail(
    client: Client,
) -> None:
    """Test creating a resource with POST request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

    client.force_login(std_usr)
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "user": admin.id,  # Referencing unpermitted OneToOneField related resource
            "name": "Some author",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


@pytest.mark.django_db
def test_create_resource_with_unpermitted_complex_related_resource_should_fail(
    client: Client,
) -> None:
    """Test creating a resource with POST request."""
    admin = User.objects.create_user(ADMIN_USER)
    std_usr = User.objects.create_user(STANDARD_USER)

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
    response = client.post(
        "/api/gated-authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
            "books": [
                book.id  # Referencing unpermitted ManyToManyRel related resource
            ],
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()
