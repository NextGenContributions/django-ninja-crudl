"""Test the API endpoints with reverse ForeignKey relation (ManyToOneRel)."""

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
    book_copy_1: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        inventory_number="B_000001",
    )
    book_copy_2: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        inventory_number="B_000002",
    )

    response = client.post(
        "/api/libraries",
        content_type="application/json",
        data={
            "name": "Some library",
            "address": "Some address",
            "book_copies": [
                book_copy_1.id,
                book_copy_2.id,
            ],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    library = models.Library.objects.get(id=response.json()["id"])
    assert library.name == "Some library"
    assert library.address == "Some address"
    assert list(library.book_copies.order_by("inventory_number")) == [
        book_copy_1,
        book_copy_2,
    ]


@pytest.mark.django_db
def test_updating_relation_with_put_should_work(client: Client) -> None:
    """Test updating a relation with PUT request."""
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
    library: models.Library = models.Library.objects.create(
        name="Some library",
        address="Some address",
    )
    book_copy: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        inventory_number="B_000001",
    )

    response = client.put(
        f"/api/libraries/{library.id}",
        content_type="application/json",
        data={
            "name": "Some updated library",
            "address": "Some updated address",
            "book_copies": [book_copy.id],
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    library.refresh_from_db()
    assert library.name == "Some updated library"
    assert library.address == "Some updated address"
    assert list(library.book_copies.order_by("inventory_number")) == [book_copy]


@pytest.mark.django_db
def test_updating_relation_with_patch_should_work(client: Client) -> None:
    """Test updating a relation with PATCH request."""
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
    library: models.Library = models.Library.objects.create(
        name="Some library",
        address="Some address",
    )
    book_copy: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        inventory_number="B_000001",
    )

    response = client.patch(
        f"/api/libraries/{library.id}",
        content_type="application/json",
        data={
            "book_copies": [book_copy.id],
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    library.refresh_from_db()
    assert library.name == "Some library"
    assert library.address == "Some address"
    assert list(library.book_copies.order_by("inventory_number")) == [book_copy]


@pytest.mark.django_db
def test_deleting_relation_by_deleting_object_should_work(client: Client) -> None:
    """Test deleting a relation with DELETE request."""
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
    library: models.Library = models.Library.objects.create(
        name="Some library",
        address="Some address",
    )
    book_copy: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        library=library,
        inventory_number="B_000001",
    )

    response = client.delete(f"/api/libraries/{library.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert not models.BookCopy.objects.filter(id=book_copy.id).exists()


@pytest.mark.django_db
def test_deleting_relation_by_patch_should_work(client: Client) -> None:
    """Test deleting a relation by using an update request."""
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
    library: models.Library = models.Library.objects.create(
        name="Some library",
        address="Some address",
    )
    book_copy: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        library=library,
        inventory_number="B_000001",
    )

    response = client.patch(
        f"/api/libraries/{library.id}",
        content_type="application/json",
        data={
            "book_copies": [],
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    library.refresh_from_db()
    assert library.name == "Some library"
    assert library.address == "Some address"
    assert list(library.book_copies.order_by("inventory_number")) == [book_copy]


@pytest.mark.django_db
def test_getting_relation_with_get_many_should_work(client: Client) -> None:
    """Test listing relations with GET many (list) request."""
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
    library: models.Library = models.Library.objects.create(
        name="Some library",
        address="Some address",
    )
    book_copy: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        library=library,
        inventory_number="B_000001",
    )

    response = client.get("/api/libraries")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Some library"
    assert response.json()[0]["address"] == "Some address"
    assert (
        response.json()[0]["book_copies"][0]["inventory_number"]
        == book_copy.inventory_number
    )


@pytest.mark.django_db
def test_getting_relation_with_get_one_should_work(client: Client) -> None:
    """Test getting relations with GET one (retrieve) request."""
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
    library: models.Library = models.Library.objects.create(
        name="Some library",
        address="Some address",
    )
    book_copy: models.BookCopy = models.BookCopy.objects.create(
        book=book,
        library=library,
        inventory_number="B_000001",
    )

    response = client.get(f"/api/libraries/{library.id}")
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert response.json()["name"] == "Some library"
    assert response.json()["address"] == "Some address"
    assert (
        response.json()["book_copies"][0]["inventory_number"]
        == book_copy.inventory_number
    )
