"""Test the API endpoints with reverse One-To-One relation."""

import datetime

import pytest
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models


@pytest.mark.django_db
def test_creating_relation_with_post_should_work(client: Client) -> None:
    """Test creating a relation with POST request."""
    publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        description="Some description",
    )

    response = client.post(
        "/api/authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
            "books": [book.id],
            # TODO(phuongfi91): The field should not be required
            "amazon_author_profile": amz_author_profile.id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    author = models.Author.objects.get(id=response.json()["id"])
    assert author.name == "Some author"
    assert author.birth_date == datetime.date(1990, 1, 1)
    assert author.amazon_author_profile.description == "Some description"


@pytest.mark.django_db
def test_updating_relation_with_put_should_work(client: Client) -> None:
    """Test updating a relation with PUT request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        description="Some description",
    )
    response = client.put(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Some updated author",
            "birth_date": "1990-01-02",
            "amazon_author_profile": amz_author_profile.id,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.name == "Some updated author"
    assert author.birth_date == datetime.date(1990, 1, 2)
    assert author.amazon_author_profile.description == "Some description"


@pytest.mark.django_db
def test_updating_relation_with_patch_should_work(client: Client) -> None:
    """Test updating a relation with PATCH request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={"amazon_author_profile": amz_author_profile.id},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.name == "Some author"
    assert author.birth_date == datetime.date(1990, 1, 1)
    assert author.amazon_author_profile.description == "Some description"


@pytest.mark.django_db
def test_deleting_relation_by_deleting_object_should_work(client: Client) -> None:
    """Test deleting a relation with DELETE request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.delete(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert not models.Author.objects.filter(id=author.id).exists()
    assert not models.AmazonAuthorProfile.objects.filter(
        id=amz_author_profile.id
    ).exists()


@pytest.mark.django_db
def test_deleting_relation_by_patch_should_work(client: Client) -> None:
    """Test deleting a relation by using an update request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            # TODO(phuongfi91): Test also updating this relation to another entity?
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/35
            "amazon_author_profile": None
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert getattr(author, "amazon_author_profile", None) is None


@pytest.mark.django_db
def test_getting_relation_with_get_many_should_work(client: Client) -> None:
    """Test listing relations with GET many (list) request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.get("/api/authors")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Some author"
    assert response.json()[0]["birth_date"] == "1990-01-01"
    assert (
        response.json()[0]["amazon_author_profile"]["description"] == "Some description"
    )
    assert response.json()[0]["user"] is None
    assert response.json()[0]["age"] == 35
    assert response.json()[0]["books_count"] == 0


@pytest.mark.django_db
def test_getting_relation_with_get_one_should_work(client: Client) -> None:
    """Test getting relations with GET one (retrieve) request."""
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    amz_author_profile = models.AmazonAuthorProfile.objects.create(
        author=author,
        description="Some description",
    )
    response = client.get(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert response.json()["name"] == "Some author"
    assert response.json()["birth_date"] == "1990-01-01"
    assert response.json()["amazon_author_profile"]["description"] == "Some description"
    assert response.json()["age"] == 35
    assert response.json()["books_count"] == 0
    assert response.json()["user"] is None
