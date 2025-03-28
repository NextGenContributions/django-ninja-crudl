"""URL configuration for the Django test project."""

from typing import override

from django.contrib import admin
from django.db.models import Q
from django.urls import path
from django.urls.resolvers import URLResolver
from django2pydantic import Infer
from ninja_extra import NinjaExtraAPI

from django_ninja_crudl import CrudlConfig, CrudlController, RequestDetails, Schema
from django_ninja_crudl.mixins.filters import FiltersMixin
from django_ninja_crudl.types import TDjangoModel
from tests.test_django.app.models import (
    Author,
    Book,
    BookCopy,
    Borrowing,
    Library,
    Publisher,
)


class DefaultFilter(FiltersMixin[TDjangoModel]):
    """Default generic filter for the CRUDL operations."""
    @override
    def get_base_filter(self, request: RequestDetails[TDjangoModel]) -> Q:
        """Return the base queryset filter that applies to all CRUDL operations."""
        return Q()

    @override
    def get_filter_for_update(self, request: RequestDetails[TDjangoModel]) -> Q:
        """Return the queryset filter that applies to the update operation."""
        return Q()

    @override
    def get_filter_for_delete(self, request: RequestDetails[TDjangoModel]) -> Q:
        """Return the queryset filter that applies to the delete operation."""
        return Q()

    @override
    def get_filter_for_list(self, request: RequestDetails[TDjangoModel]) -> Q:
        """Return the queryset filter that applies to the list operation."""
        return Q()

    @override
    def get_filter_for_get_one(self, request: RequestDetails[TDjangoModel]) -> Q:
        """Return the queryset filter that applies to the get_one operation."""
        return Q()


class AuthorCrudl(CrudlController[Author], DefaultFilter[Author]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Author model."""
    config = CrudlConfig[Author](
        model=Author,
        base_path="/authors",
        create_schema=Schema[Author](
            fields={
                "name": Infer,
                "birth_date": Infer,
                # TODO(phuongfi91): support reverse relation handler
                #  https://github.com/NextGenContributions/django-ninja-crudl/issues/11
                # "books": Infer,
            }
        ),
        update_schema=Schema[Author](
            fields={
                "name": Infer,
                "birth_date": Infer,
                # TODO(phuongfi91): support reverse relation handler
                #  https://github.com/NextGenContributions/django-ninja-crudl/issues/11
                # "books": Infer,
            }
        ),
        get_one_schema=Schema[Author](
            fields={
                "id": Infer,
                "name": Infer,
                "birth_date": Infer,
                "age": Infer,
                "books_count": Infer,
                "books": {"id": Infer, "title": Infer},
            }
        ),
        list_schema=Schema[Author](
            fields={
                "id": Infer,
                "name": Infer,
                "birth_date": Infer,
                "age": Infer,
                "books_count": Infer,
                "books": {"id": Infer, "title": Infer},
            }
        ),
        delete_allowed=True,
    )


class PublisherCrudl(CrudlController[Publisher], DefaultFilter[Publisher]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Publisher model."""
    config = CrudlConfig[Publisher](
        model=Publisher,
        base_path="/publishers",
        create_schema=Schema[Publisher](
            # TODO(phuongfi91): Test for alternative syntax
            #  https://github.com/NextGenContributions/django-ninja-crudl/issues/13
            # fields=[
            #     "name",
            #     "address",
            # ]
            fields={
                "name": Infer,
                "address": Infer,
                "publisher_type": Infer,
            }
        ),
        update_schema=Schema[Publisher](
            fields={
                "name": Infer,
                "address": Infer,
            }
        ),
        get_one_schema=Schema[Publisher](
            fields={
                "id": Infer,
                "name": Infer,
                "address": Infer,
            }
        ),
        list_schema=Schema[Publisher](
            fields={
                "id": Infer,
                "name": Infer,
                "address": Infer,
            }
        ),
        delete_allowed=True,
    )


class BookCrudl(CrudlController[Book], DefaultFilter[Book]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Book model."""
    config = CrudlConfig[Book](
        model=Book,
        base_path="/books",
        create_schema=Schema[Book](
            fields={
                "title": Infer,
                "isbn": Infer,
                "publication_date": Infer,
                "publisher_id": Infer,
                "authors": Infer,
            }
        ),
        update_schema=Schema[Book](
            fields={
                "title": Infer,
                "isbn": Infer,
                "publication_date": Infer,
                "publisher_id": Infer,
                "authors": Infer,
                # TODO(phuongfi91): support 'publisher' and infer it as 'publisher_id'
                #  adding 'publisher' field now would cause HTTP 422
                # "publisher": Infer,
            }
        ),
        get_one_schema=Schema[Book](
            fields={
                "id": Infer,
                "title": Infer,
                "isbn": Infer,
                "publication_date": Infer,
                "authors": {"id": Infer, "name": Infer, "birth_date": Infer},
                "publisher": {"id": Infer, "name": Infer},
            }
        ),
        list_schema=Schema[Book](
            fields={
                "id": Infer,
                "title": Infer,
                "isbn": Infer,
                "publication_date": Infer,
                "publisher": {"id": Infer, "name": Infer},
                "authors": {"id": Infer, "name": Infer},
            }
        ),
        delete_allowed=True,
        # TODO(phuongfi91): implement 'search_fields'
        #  https://github.com/NextGenContributions/django-ninja-crudl/issues/33
        #  search_fields: ClassVar[list[str]] = [
        #      "title",
        #      "isbn",
        #      "authors__name",
        #      "publisher__name",
        #      "publication_date",
        #  ]
    )


class LibraryCrudl(CrudlController[Library], DefaultFilter[Library]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Library model."""
    config = CrudlConfig[Library](
        model=Library,
        base_path="/libraries",
        create_schema=Schema[Library](
            fields={
                "name": Infer,
                "address": Infer,
            }
        ),
        update_schema=Schema[Library](
            fields={
                "name": Infer,
                "address": Infer,
            }
        ),
        get_one_schema=Schema[Library](
            fields={
                "id": Infer,
                "name": Infer,
                "address": Infer,
            }
        ),
        list_schema=Schema[Library](
            fields={
                "id": Infer,
                "name": Infer,
                "address": Infer,
            }
        ),
    )


class BookCopyCrudl(CrudlController[BookCopy], DefaultFilter[BookCopy]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the BookCopy model."""
    config = CrudlConfig[BookCopy](
        model=BookCopy,
        base_path="/book_copies",
        create_schema=Schema[BookCopy](
            fields={
                "book_id": Infer,
                "library_id": Infer,
                "inventory_number": Infer,
            }
        ),
        update_schema=Schema[BookCopy](
            fields={
                "book_id": Infer,
                "library_id": Infer,
                "inventory_number": Infer,
            }
        ),
        get_one_schema=Schema[BookCopy](
            fields={
                "id": Infer,
                "book": {"id": Infer, "title": Infer},
                "library": {"id": Infer, "name": Infer, "address": Infer},
                "inventory_number": Infer,
            }
        ),
        list_schema=Schema[BookCopy](
            fields={
                "id": Infer,
                "book": {"id": Infer, "title": Infer},
                "library": {"id": Infer, "name": Infer},
                "inventory_number": Infer,
            }
        ),
    )


class BorrowingCrudl(CrudlController[Borrowing], DefaultFilter[Borrowing]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Borrowing model."""
    config = CrudlConfig[Borrowing](
        model=Borrowing,
        base_path="/borrowings",
        create_schema=Schema[Borrowing](
            fields={
                "user_id": Infer,
                "book_copy_id": Infer,
                "borrow_date": Infer,
            }
        ),
        update_schema=Schema[Borrowing](
            fields={
                "return_date": Infer,
            }
        ),
        get_one_schema=Schema[Borrowing](
            fields={
                "id": Infer,
                "user": {"id": Infer},
                "book_copy": {"id": Infer},
                "borrow_date": Infer,
                "return_date": Infer,
            }
        ),
        list_schema=Schema[Borrowing](
            fields={
                "id": Infer,
                "user": {"id": Infer},
                "book_copy": {"id": Infer},
                "borrow_date": Infer,
                "return_date": Infer,
            }
        ),
    )


api = NinjaExtraAPI()

api.register_controllers(PublisherCrudl)
api.register_controllers(BookCrudl)
api.register_controllers(AuthorCrudl)
api.register_controllers(BookCopyCrudl)
api.register_controllers(BorrowingCrudl)
api.register_controllers(LibraryCrudl)


urlpatterns: list[URLResolver] = [
    path("api/", api.urls),
    path("admin/", admin.site.urls),
]
