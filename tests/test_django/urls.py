"""URL configuration for the Django test project."""

from django.contrib import admin
from django.urls import path
from django.urls.resolvers import URLResolver
from ninja_extra import NinjaExtraAPI

from django_ninja_crudl.crudl import Crudl
from tests.test_django.app import models


class AuthorCrudl(Crudl):
    """CRUDL for the Author model."""

    class Meta(Crudl.Meta):
        """Configuration for the CRUDL API."""

        model_class = models.Author
        base_path = "/authors"


class PublisherCrudl(Crudl):
    """CRUDL for the Publisher model."""

    class Meta(Crudl.Meta):
        """Configuration for the CRUDL API."""

        model_class = models.Publisher
        base_path = "/publishers"


class BookCrudl(Crudl):
    """CRUDL for the Book model."""

    class Meta(Crudl.Meta):
        """Configuration for the CRUDL API."""

        model_class = models.Book
        base_path = "/books"


class BookCopyCrudl(Crudl):
    """CRUDL for the BookCopy model."""

    class Meta(Crudl.Meta):
        """Configuration for the CRUDL API."""

        model_class = models.BookCopy
        base_path = "/book_copies"


class BorrowingCrudl(Crudl):
    """CRUDL for the Borrowing model."""

    class Meta(Crudl.Meta):
        """Configuration for the CRUDL API."""

        model_class = models.Borrowing
        base_path = "/borrowings"


class LibraryCrudl(Crudl):
    """CRUDL for the Library model."""

    class Meta(Crudl.Meta):
        """Configuration for the CRUDL API."""

        model_class = models.Library
        base_path = "/libraries"


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
