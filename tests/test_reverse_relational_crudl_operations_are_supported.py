"""Test the API endpoints with reverse relational data."""

import datetime

import pytest
from django.test import Client
from ninja_extra import status

from tests.test_django.app import models


@pytest.mark.django_db
def test_creating_relation_with_post_should_work(client: Client) -> None:
    """Test creating a relation with POST request."""
    publisher: models.Publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    book: models.Book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )

    response = client.post(
        "/api/authors",
        content_type="application/json",
        data={
            "name": "Some author",
            "birth_date": "1990-01-01",
            "books": [book.id],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    author = models.Author.objects.get(id=response.json()["id"])
    assert author.name == "Some author"
    assert author.birth_date == datetime.date(1990, 1, 1)
    assert list(author.books.order_by("title")) == [book]


@pytest.mark.django_db
def test_updating_relation_with_put_should_work(client: Client) -> None:
    """Test updating a relation with PUT request."""
    publisher: models.Publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author: models.Author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    book: models.Book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )

    response = client.put(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "name": "Updated author",
            "birth_date": "1991-01-01",
            "books": [book.id],
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert author.name == "Updated author"
    assert author.birth_date == datetime.date(1991, 1, 1)
    assert list(author.books.order_by("title")) == [book]


@pytest.mark.django_db
def test_updating_relation_with_patch_should_work(client: Client) -> None:
    """Test updating a relation with PATCH request."""
    publisher: models.Publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author: models.Author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    book: models.Book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )

    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "books": [book.id],
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert list(author.books.order_by("title")) == [book]


@pytest.mark.django_db
def test_deleting_relation_by_deleting_object_should_work(client: Client) -> None:
    """Test deleting a relation with DELETE request."""
    publisher: models.Publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author: models.Author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    book: models.Book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )
    book.authors.set([author])
    author_id = author.id
    book_id = book.id
    publisher_id = publisher.id

    response = client.delete(f"/api/authors/{author_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert not models.Author.objects.filter(id=author_id).exists()
    assert models.Book.objects.filter(id=book_id).exists()
    assert models.Publisher.objects.filter(id=publisher_id).exists()


@pytest.mark.django_db
def test_deleting_relation_by_patch_should_work(client: Client) -> None:
    """Test deleting a relation by using an update request."""
    publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )
    book.authors.set([author])

    response = client.patch(
        f"/api/authors/{author.id}",
        content_type="application/json",
        data={
            "books": [],
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    author.refresh_from_db()
    assert not author.books.exists()


@pytest.mark.django_db
def test_getting_relation_with_get_many_should_work(client: Client) -> None:
    """Test listing relations with GET many (list) request."""
    publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author_1 = models.Author.objects.create(
        name="Some author 1",
        birth_date="1990-01-01",
    )
    author_2 = models.Author.objects.create(
        name="Some author 2",
        birth_date="1991-01-01",
    )
    book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )
    book.authors.set([author_1, author_2])

    response = client.get("/api/authors")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Some author 1"
    assert response.json()[0]["birth_date"] == "1990-01-01"
    assert response.json()[0]["books_count"] == 1
    assert response.json()[0]["books"][0]["id"] == book.id
    assert response.json()[0]["books"][0]["title"] == "Some book"
    assert response.json()[1]["books_count"] == 1
    assert response.json()[1]["name"] == "Some author 2"
    assert response.json()[1]["birth_date"] == "1991-01-01"
    assert response.json()[1]["books"][0]["id"] == book.id
    assert response.json()[1]["books"][0]["title"] == "Some book"


@pytest.mark.django_db
def test_getting_relation_with_get_one_should_work(client: Client) -> None:
    """Test getting relations with GET one (retrieve) request."""
    publisher = models.Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    author: models.Author = models.Author.objects.create(
        name="Some author",
        birth_date="1990-01-01",
    )
    book = models.Book.objects.create(
        title="Some book",
        isbn="9783161484100",
        publication_date="2021-01-01",
        publisher=publisher,
    )
    book.authors.set([author])

    response = client.get(f"/api/authors/{author.id}")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert response.json()["name"] == "Some author"
    assert response.json()["birth_date"] == "1990-01-01"
    assert response.json()["books_count"] == 1
    assert response.json()["books"][0]["id"] == book.id
    assert response.json()["books"][0]["title"] == "Some book"
    assert "isbn" not in response.json()["books"][0]
    assert "publication_date" not in response.json()["books"][0]
