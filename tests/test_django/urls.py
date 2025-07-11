"""URL configuration for the Django test project."""

from typing import cast, override

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import path
from django.urls.resolvers import URLResolver
from django.utils import timezone

from django_ninja_crudl import (
    BasePermission,
    CrudlConfig,
    CrudlController,
    Infer,
    RequestDetails,
    Schema,
)
from django_ninja_crudl.api import NinjaCrudlAPI
from django_ninja_crudl.mixins.filters import FiltersMixin
from django_ninja_crudl.types import TDjangoModel
from tests.test_django.app.models import (
    AmazonAuthorProfile,
    Author,
    BaseModel,
    Book,
    BookCopy,
    Borrowing,
    Library,
    Publisher,
)

ADMIN_USER = "john_doe"
STANDARD_USER = "jane_doe"
RESTRICTED_USER = "average_joe"


class HasResourcePermissions(BasePermission[TDjangoModel]):
    """Check if the user has permissions to access the resource."""

    @override
    def is_authenticated(self, request: RequestDetails[TDjangoModel]) -> bool:
        if not getattr(request.request, "user", False):
            return False
        return isinstance(request.request.user, User)

    @override
    def has_permission(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user has permission to perform the action."""
        user = cast("User", request.request.user)

        if user.username in [ADMIN_USER, STANDARD_USER]:  # pyright: ignore [reportUnknownMemberType]
            return True

        return False

    @override
    def has_object_permission(self, request: RequestDetails[TDjangoModel]) -> bool:
        """Check if the user has permission to perform the action on the object."""
        user = cast("User", request.request.user)

        if user.username == ADMIN_USER:  # pyright: ignore [reportUnknownMemberType]
            return True

        if user.username == STANDARD_USER:  # pyright: ignore [reportUnknownMemberType]
            # Check if the user is the owner of the object
            if request.object and hasattr(request.object, "created_by"):
                obj = cast("BaseModel", request.object)
                return obj.created_by == user  # pyright: ignore [reportUnknownVariableType, reportUnknownMemberType]

        return False

    @override
    def has_related_object_permission(
        self, request: RequestDetails[TDjangoModel]
    ) -> bool:
        """Check if the user has permission to perform the action on related object."""
        user = cast("User", request.request.user)

        if user.username == ADMIN_USER:  # pyright: ignore [reportUnknownMemberType]
            return True

        if user.username == STANDARD_USER:  # pyright: ignore [reportUnknownMemberType]
            # Check if the user is the owner of the object
            if request.related_object and hasattr(request.related_object, "created_by"):
                obj = cast("BaseModel", request.related_object)
                return obj.created_by == user  # pyright: ignore [reportUnknownVariableType, reportUnknownMemberType]

        return False


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


class GatedAuthorCrudl(CrudlController[Author], DefaultFilter[Author]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Author model, with permission gating."""

    @override
    def post_create(self, request: RequestDetails[TDjangoModel]) -> None:
        """Pre-create hook to check permissions before creating an author."""
        if not request.object:
            msg = "Created object is not set."
            raise ValueError(msg)

        if not getattr(request.request, "user", False) or not isinstance(
            request.request.user, User
        ):
            msg = "Missing or invalid user."
            raise ValueError(msg)

        if type(request.object) is BaseModel:
            request.object.created_at = timezone.now()
            request.object.created_by = request.request.user
            request.object.save()

    @override
    def get_filter_for_list(self, request: RequestDetails[TDjangoModel]) -> Q:
        """Return the queryset filter that applies to the list operation."""
        user = cast("User", request.request.user)

        if user.username == ADMIN_USER:  # pyright: ignore [reportUnknownMemberType]
            return Q()

        if user.username == STANDARD_USER:  # pyright: ignore [reportUnknownMemberType]
            return Q(created_by=user)

        # Return nothing
        return Q(pk=None)

    config = CrudlConfig[Author](
        model=Author,
        base_path="/gated-authors",
        permission_classes=[HasResourcePermissions],
        create_operation_id="GatedAuthor_create",
        create_schema=Schema[Author](
            fields={
                "user": Infer,
                "name": Infer,
                "birth_date": Infer,
                "books": Infer,
                "amazon_author_profile": Infer,
            }
        ),
        partial_update_operation_id="GatedAuthor_partial_update",
        update_operation_id="GatedAuthor_update",
        update_schema=Schema[Author](
            fields={
                "user": Infer,
                "name": Infer,
                "birth_date": Infer,
                "books": Infer,
                "amazon_author_profile": Infer,
            }
        ),
        get_one_operation_id="GatedAuthor_get_one",
        get_one_schema=Schema[Author](
            fields={
                "id": Infer,
                "name": Infer,
                "birth_date": Infer,
                "age": Infer,
                "books_count": Infer,
                "books": {"id": Infer, "title": Infer},
                "amazon_author_profile": {"description": Infer},
            }
        ),
        list_operation_id="GatedAuthor_list",
        list_schema=Schema[Author](
            fields={
                "id": Infer,
                "name": Infer,
                "birth_date": Infer,
                "age": Infer,
                "books_count": Infer,
                "books": {"id": Infer, "title": Infer},
                "amazon_author_profile": {"description": Infer},
            }
        ),
        delete_operation_id="GatedAuthor_delete",
        delete_allowed=True,
    )


class AuthorCrudl(CrudlController[Author], DefaultFilter[Author]):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the Author model."""

    config = CrudlConfig[Author](
        model=Author,
        base_path="/authors",
        create_schema=Schema[Author](
            fields={
                "name": Infer,
                "birth_date": Infer,
                "books": Infer,
                "amazon_author_profile": Infer,
            }
        ),
        update_schema=Schema[Author](
            fields={
                "name": Infer,
                "birth_date": Infer,
                "books": Infer,
                "amazon_author_profile": Infer,
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
                "amazon_author_profile": {"description": Infer},
                "user": {"first_name": Infer, "last_name": Infer},
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
                "amazon_author_profile": {"description": Infer},
                "user": {"first_name": Infer, "last_name": Infer},
            }
        ),
        delete_allowed=True,
    )


class AmazonAuthorProfileCrudl(
    CrudlController[AmazonAuthorProfile], DefaultFilter[AmazonAuthorProfile]
):  # pylint: disable=too-many-ancestors
    """CRUDL controller for the AmazonAuthorProfile model."""

    config = CrudlConfig[AmazonAuthorProfile](
        model=AmazonAuthorProfile,
        base_path="/amazon_author_profiles",
        create_schema=Schema[AmazonAuthorProfile](
            fields={
                "author": Infer,
                "profile_url": Infer,
                "description": Infer,
            }
        ),
        update_schema=Schema[AmazonAuthorProfile](
            fields={
                "author": Infer,
                "profile_url": Infer,
                "description": Infer,
            }
        ),
        get_one_schema=Schema[AmazonAuthorProfile](
            fields={
                "id": Infer,
                "author": {"id": Infer, "name": Infer},
                "profile_url": Infer,
                "description": Infer,
            }
        ),
        list_schema=Schema[AmazonAuthorProfile](
            fields={
                "id": Infer,
                "author": {"id": Infer, "name": Infer},
                "profile_url": Infer,
                "description": Infer,
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
                # "publisher_id": Infer,
                "authors": Infer,
                # TODO(phuongfi91): support 'publisher' and infer it as 'publisher_id'
                #  adding 'publisher' field now would cause HTTP 422
                "publisher": Infer,
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
                "book_copies": Infer,
            }
        ),
        update_schema=Schema[Library](
            fields={
                "name": Infer,
                "address": Infer,
                "book_copies": Infer,
            }
        ),
        get_one_schema=Schema[Library](
            fields={
                "id": Infer,
                "name": Infer,
                "address": Infer,
                "book_copies": {
                    "inventory_number": Infer,
                },
            }
        ),
        list_schema=Schema[Library](
            fields={
                "id": Infer,
                "name": Infer,
                "address": Infer,
                # TODO(phuongfi91): Test also this case
                #  https://github.com/NextGenContributions/django-ninja-crudl/issues/11
                # "book_copies": Infer,
                "book_copies": {
                    "inventory_number": Infer,
                },
            }
        ),
        delete_allowed=True,
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


api = NinjaCrudlAPI()

api.register_controllers(PublisherCrudl)
api.register_controllers(BookCrudl)
api.register_controllers(GatedAuthorCrudl)
api.register_controllers(AuthorCrudl)
api.register_controllers(AmazonAuthorProfileCrudl)
api.register_controllers(BookCopyCrudl)
api.register_controllers(BorrowingCrudl)
api.register_controllers(LibraryCrudl)


urlpatterns: list[URLResolver] = [
    path("api/", api.urls),
    path("admin/", admin.site.urls),
]
