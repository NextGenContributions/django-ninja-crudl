"""Test soft-delete functionality.

Querying through 'objects' manager should raise DoesNotExist, while querying
through 'all_objects' manager should still return the soft-deleted objects.
"""

from typing import cast

import pytest
from django.contrib.auth.models import User
from django.db.models import Model
from django.test import Client
from django.utils import timezone
from ninja_extra import status

from tests.test_django.app.models import (
    Author,
    BaseModel,
    Book,
    BookCopy,
    Borrowing,
    Library,
    Publisher,
    PublisherWebsite,
    UserFavoriteBook,
)


def assert_soft_deleted(
    obj: BaseModel | Model, expected_deleter: User | None = None
) -> None:
    """Assert that an object is soft deleted."""
    model_class = obj.__class__
    obj_id = cast("int", obj.pk)

    # Object should NOT exist via default objects manager
    with pytest.raises(model_class.DoesNotExist):
        model_class.objects.get(id=obj_id)

    if not issubclass(model_class, BaseModel):
        return

    # Object should exist via all_objects
    refreshed_obj = model_class.all_objects.get(id=obj_id)

    # Soft delete fields should be set
    assert refreshed_obj.deleted is True, (
        f"{model_class.__name__} should be marked as deleted"
    )
    assert refreshed_obj.deleted_at is not None, (
        f"{model_class.__name__} should have deleted_at timestamp"
    )
    if expected_deleter is not None:
        assert refreshed_obj.deleted_by == expected_deleter, (
            f"{model_class.__name__} should be deleted by expected user"
        )


def assert_exists(obj: BaseModel | Model) -> None:
    """Assert that an object exists (is not soft-deleted)."""
    model_class = obj.__class__
    obj_id = cast("int", obj.pk)

    # Retrieve the object again
    # Object should exist via default objects manager
    refreshed_obj = model_class.objects.filter(id=obj_id).first()
    assert refreshed_obj is not None, f"{model_class.__name__} should exist"

    if not isinstance(refreshed_obj, BaseModel):
        return

    # Soft delete fields should NOT be set
    assert refreshed_obj.deleted is False, (
        f"{model_class.__name__} should not be marked as deleted"
    )
    assert refreshed_obj.deleted_at is None, (
        f"{model_class.__name__} should not have deleted_at timestamp"
    )
    assert refreshed_obj.deleted_by is None, (
        f"{model_class.__name__} should not have deleted_by user"
    )


@pytest.mark.django_db
def test_soft_delete_single_resource_works(client: Client) -> None:
    """Test deleting a single resource with DELETE request."""
    p = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    response = client.delete(f"/api/soft-delete-publishers/{p.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert_soft_deleted(p)


@pytest.mark.django_db
def test_soft_delete_related_resources_works(client: Client) -> None:
    """Test deleting a resource which has related resources with DELETE request."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    library = Library.objects.create(name="Main Library", address="Library address")
    user = User.objects.create(username="borrower")

    # Related objects that should be cascade-deleted
    website = PublisherWebsite.objects.create(
        publisher=p,
        url="https://some-publisher.com",
    )
    book = Book.objects.create(
        title="Some book",
        isbn="0000000000001",
        publication_date=timezone.now().date(),
        publisher=p,
    )

    # Perform soft-delete on the main publisher object
    deleter = User.objects.create(username="deleter")
    client.force_login(deleter)
    response = client.delete(f"/api/soft-delete-publishers/{p.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()

    # Main publisher object should be soft-deleted
    assert_soft_deleted(p, expected_deleter=deleter)

    # Related objects should also be soft-deleted via CASCADE
    assert_soft_deleted(website, expected_deleter=deleter)
    assert_soft_deleted(book, expected_deleter=deleter)

    # Un-related objects should NOT be deleted
    assert_exists(library)
    assert_exists(user)


@pytest.mark.django_db
def test_soft_delete_related_protected_resources_should_not_works(
    client: Client,
) -> None:
    """Test deleting a resource which has PROTECT constraint on related resources."""
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )

    # Related objects that should be cascade-deleted
    book = Book.objects.create(
        title="Some book",
        isbn="0000000000001",
        publication_date=timezone.now().date(),
        publisher=p,
    )
    book_copy = BookCopy.objects.create(book=book, inventory_number="INV-1")

    # Perform soft-delete on the main publisher object
    deleter = User.objects.create(username="deleter")
    client.force_login(deleter)
    response = client.delete(f"/api/soft-delete-publishers/{p.id}")
    assert response.status_code == status.HTTP_409_CONFLICT, response.json()

    # Main publisher object should NOT be soft-deleted
    assert_exists(p)

    # Related objects should also NOT be soft-deleted via CASCADE
    assert_exists(book)
    assert_exists(book_copy)


@pytest.mark.django_db
def test_soft_delete_related_restricted_resources_should_works_appropriately(
    client: Client,
) -> None:
    """Test deleting a resource which has RESTRICT constraint on related resources.

    This test references the example of RESTRICT constraint documented at:
    https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.RESTRICT
    """
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )
    user = User.objects.create(username="borrower")
    library = Library.objects.create(name="Main Library", address="Library address")

    # Related objects that should be cascade-deleted
    book = Book.objects.create(
        title="Some book",
        isbn="0000000000001",
        publication_date=timezone.now().date(),
        publisher=p,
    )
    book_copy = BookCopy.objects.create(
        book=book,
        library=library,
        inventory_number="INV-1",
    )
    borrowing = Borrowing.objects.create(
        user=user,
        library=library,
        book_copy=book_copy,
        borrow_date=timezone.now().date(),
    )

    # Prepare deleter user
    deleter = User.objects.create(username="deleter")
    client.force_login(deleter)

    # Performing soft-delete on a BookCopy object should FAIL due to RESTRICT constraint
    # on Borrowing model when deleting BookCopy
    response = client.delete(f"/api/soft-delete-book-copies/{book_copy.id}")
    assert response.status_code == status.HTTP_409_CONFLICT, response.json()
    # BookCopy object should NOT be soft-deleted
    assert_exists(book_copy)
    # Related objects should also NOT be soft-deleted via CASCADE
    assert_exists(borrowing)

    # HOWEVER, performing soft-delete on a Library object should SUCCEED since deleting
    # a Library would also CASCADE delete both BookCopy and Borrowing at the same time
    response = client.delete(f"/api/soft-delete-libraries/{library.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    # Library object should be soft-deleted
    assert_soft_deleted(library, expected_deleter=deleter)
    # Related objects should also be soft-deleted via CASCADE
    assert_soft_deleted(book_copy, expected_deleter=deleter)
    assert_soft_deleted(borrowing, expected_deleter=deleter)

    # Un-related objects should NOT be deleted
    assert_exists(user)
    assert_exists(p)
    assert_exists(book)


@pytest.mark.django_db
def test_soft_delete_m2m_related_resource_with_auto_created_through_model_works(
    client: Client,
) -> None:
    """Test deleting a resource which has m2m related objects with DELETE request.

    The m2m related objects are linked via an auto-created through model.
    """
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )

    # Many-to-many related authors
    author1 = Author.objects.create(name="Author One")
    author2 = Author.objects.create(name="Author Two")

    # Related objects that should be cascade-deleted
    book = Book.objects.create(
        title="Some book",
        isbn="0000000000001",
        publication_date=timezone.now().date(),
        publisher=p,
    )
    book.authors.add(author1, author2)
    m2m_rel1 = book.authors.through.objects.get(author=author1, book=book)
    m2m_rel2 = book.authors.through.objects.get(author=author2, book=book)

    # Perform soft-delete on the main publisher object
    deleter = User.objects.create(username="deleter")
    client.force_login(deleter)
    response = client.delete(f"/api/soft-delete-publishers/{p.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()

    # Main publisher object should be soft-deleted
    assert_soft_deleted(p, expected_deleter=deleter)

    # Related objects should also be soft-deleted via CASCADE
    assert_soft_deleted(book, expected_deleter=deleter)

    # These calls should not raise exceptions since m2m authors are not soft-deleted
    author1.refresh_from_db()
    author2.refresh_from_db()
    # Authors should remain but their m2m links to books are HARD-deleted
    with pytest.raises(book.authors.through.DoesNotExist):
        m2m_rel1.refresh_from_db()
    with pytest.raises(book.authors.through.DoesNotExist):
        m2m_rel2.refresh_from_db()
    assert author1.books_count == 0
    assert author2.books_count == 0


@pytest.mark.django_db
def test_soft_delete_m2m_related_resource_with_custom_through_model_works(
    client: Client,
) -> None:
    """Test deleting a resource which has m2m related objects with DELETE request.

    The m2m related objects are linked via a custom through model.
    """
    p: Publisher = Publisher.objects.create(
        name="Some publisher",
        address="Some address",
    )

    # Many-to-many related users who favorite the publisher's books
    user1 = User.objects.create(username="user1")
    user2 = User.objects.create(username="user2")

    # Related objects that should be cascade-deleted
    book = Book.objects.create(
        title="Some book",
        isbn="0000000000001",
        publication_date=timezone.now().date(),
        publisher=p,
    )
    book.favorite_users.add(user1, user2)
    m2m_rel1 = UserFavoriteBook.objects.get(user=user1, book=book)
    m2m_rel2 = UserFavoriteBook.objects.get(user=user2, book=book)

    # Perform soft-delete on the main publisher object
    deleter = User.objects.create(username="deleter")
    client.force_login(deleter)
    response = client.delete(f"/api/soft-delete-publishers/{p.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()

    # Main publisher object should be soft-deleted
    assert_soft_deleted(p, expected_deleter=deleter)

    # Related objects should also be soft-deleted via CASCADE
    assert_soft_deleted(book, expected_deleter=deleter)

    # These calls should not raise exceptions since m2m users are not soft-deleted
    user1.refresh_from_db()
    user2.refresh_from_db()
    # Users should remain but their m2m links to books are SOFT-deleted
    assert_soft_deleted(m2m_rel1, expected_deleter=deleter)
    assert_soft_deleted(m2m_rel2, expected_deleter=deleter)
    assert user1.favorite_book_relations.count() == 0  # type: ignore[attr-defined]
    assert user2.favorite_book_relations.count() == 0  # type: ignore[attr-defined]
