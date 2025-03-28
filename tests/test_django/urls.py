"""URL configuration for the Django test project."""

from typing import override

from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse, HttpRequest
from django.urls import path, Resolver404
from django.urls.resolvers import URLResolver
from django2pydantic import Infer
from ninja_extra import NinjaExtraAPI

from django_ninja_crudl import CrudlConfig, CrudlController, RequestDetails, Schema
from django_ninja_crudl.mixins.filters import FiltersMixin
from tests.test_django.app.models import (
    Author,
    Book,
    BookCopy,
    Borrowing,
    Library,
    Publisher,
)


class DefaultFilter(FiltersMixin):
    @override
    def get_base_filter(self, request: RequestDetails) -> Q:
        """Return the base queryset filter that applies to all CRUDL operations."""
        return Q()

    @override
    def get_filter_for_update(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the update operation."""
        # return self.get_filter(request, 'change')
        return Q()

    @override
    def get_filter_for_delete(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the delete operation."""
        # return self.get_filter(request, 'delete')
        return Q()

    @override
    def get_filter_for_list(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the list operation."""
        # return self.get_filter(request, "view")
        return Q()

    @override
    def get_filter_for_get_one(self, request: RequestDetails) -> Q:
        """Return the queryset filter that applies to the get_one operation."""
        # return self.get_filter(request, 'view')
        return Q()


class AuthorCrudl(CrudlController[Author], DefaultFilter):
    config = CrudlConfig[Author](
        model=Author,
        base_path="/authors",
        create_schema=Schema[Author](
            fields={
                "name": Infer,
                "birth_date": Infer,
            }
        ),
        update_schema=Schema[Author](
            fields={
                "name": Infer,
                "birth_date": Infer,
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
            }
        ),
    )


class PublisherCrudl(CrudlController[Publisher], DefaultFilter):
    config = CrudlConfig[Publisher](
        model=Publisher,
        base_path="/publishers",
        create_schema=Schema[Publisher](
            # TODO(phuongfi91): Test for alternative syntax
            # fields=[
            #     "name",
            #     "address",
            # ]
            fields={
                "name": Infer,
                "address": Infer,
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


class BookCrudl(CrudlController[Book], DefaultFilter):
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
        #     search_fields: ClassVar[list[str]] = [
        #         "title",
        #         "isbn",
        #         "authors__name",
        #         "publisher__name",
        #         "publication_date",
        #     ]
    )


class LibraryCrudl(CrudlController[Library], DefaultFilter):
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


class BookCopyCrudl(CrudlController[BookCopy], DefaultFilter):
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


class BorrowingCrudl(CrudlController[Borrowing], DefaultFilter):
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
