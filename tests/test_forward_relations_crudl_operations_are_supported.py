"""Test the API endpoints with forward ForeignKey/Many-to-Many relations."""

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
    author_1: models.Author = models.Author.objects.create(
        name="Some author 1",
        birth_date="1990-01-01",
    )
    author_2: models.Author = models.Author.objects.create(
        name="Some author 2",
        birth_date="1991-01-01",
    )

    response = client.post(
        "/api/books",
        content_type="application/json",
        data={
            "title": "Some book",
            "isbn": "9783161484100",
            "publication_date": "2021-01-01",
            "publisher_id": publisher.id,
            "authors": [
                author_1.id,
                author_2.id,
            ],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    book = models.Book.objects.get(id=response.json()["id"])
    assert book.title == "Some book"
    assert book.publisher == publisher
    assert list(book.authors.order_by("name")) == [author_1, author_2]


@pytest.mark.django_db
def test_updating_relation_with_put_should_work(client: Client) -> None:
    """Test updating a relation with PUT request."""
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

    new_publisher = models.Publisher.objects.create(
        name="New publisher",
        address="New address",
    )
    new_author_1 = models.Author.objects.create(
        name="New author 1",
        birth_date="1990-01-01",
    )
    new_author_2 = models.Author.objects.create(
        name="New author 2",
        birth_date="1991-01-01",
    )

    response = client.put(
        f"/api/books/{book.id}",
        content_type="application/json",
        data={
            "title": "Updated book",
            "isbn": "9783161484101",
            "publication_date": "2022-01-01",
            "publisher_id": new_publisher.id,
            "authors": [
                new_author_1.id,
                new_author_2.id,
            ],
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    book.refresh_from_db()
    assert book.title == "Updated book"
    assert book.publisher == new_publisher
    assert list(book.authors.order_by("name")) == [new_author_1, new_author_2]


@pytest.mark.django_db
def test_updating_relation_with_patch_should_work(client: Client) -> None:
    """Test updating a relation with PATCH request."""
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

    new_publisher = models.Publisher.objects.create(
        name="New publisher",
        address="New address",
    )
    new_author = models.Author.objects.create(
        name="New author",
        birth_date="1990-01-01",
    )

    response = client.patch(
        f"/api/books/{book.id}",
        content_type="application/json",
        data={
            "publisher_id": new_publisher.id,
            "authors": [new_author.id],
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    book.refresh_from_db()
    assert book.publisher == new_publisher
    assert list(book.authors.all()) == [new_author]


@pytest.mark.django_db
def test_deleting_relation_by_deleting_object_should_work(client: Client) -> None:
    """Test deleting a relation with DELETE request."""
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
    author_id = author.id
    book_id = book.id
    publisher_id = publisher.id

    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert not models.Book.objects.filter(id=book_id).exists()
    assert models.Author.objects.filter(id=author_id).exists()
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
        f"/api/books/{book.id}",
        content_type="application/json",
        data={
            "authors": [],
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert not book.authors.exists()


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

    response = client.get("/api/books")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Some book"
    assert response.json()[0]["publisher"]["name"] == "Some publisher"
    assert response.json()[0]["authors"][0]["name"] == "Some author 1"
    assert response.json()[0]["authors"][1]["name"] == "Some author 2"


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

    response = client.get(f"/api/books/{book.id}")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert response.json()["title"] == "Some book"
    assert response.json()["publisher"]["name"] == "Some publisher"
    assert "address" not in response.json()["publisher"]
    assert response.json()["authors"][0]["name"] == "Some author"
    assert response.json()["authors"][0]["birth_date"] == "1990-01-01"
    assert "age" not in response.json()["authors"][0]
