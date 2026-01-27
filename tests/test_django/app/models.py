"""Models for the Django test project."""

from datetime import UTC, date, datetime
from typing import ClassVar, Self, cast, final, override

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django2pydantic.types import TDjangoModel
from pydantic import HttpUrl


class SoftDeleteManager(models.Manager[TDjangoModel]):
    """Manager that filters out soft-deleted objects by default."""

    @override
    def get_queryset(
        self,
    ) -> models.QuerySet[TDjangoModel]:  # ty:ignore[invalid-type-arguments]
        """Return queryset excluding soft-deleted objects."""
        return super().get_queryset().filter(deleted=False)


class BaseModel(models.Model):
    """Base model with common fields for all models."""

    id: int  # Just for type hinting

    created_at = models.DateTimeField[datetime, datetime](auto_now_add=True)
    created_by = models.ForeignKey["User | None", "User | None"](
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    deleted = models.BooleanField[bool, bool](default=False)
    deleted_at = models.DateTimeField[datetime | None, datetime | None](
        null=True, blank=True
    )
    deleted_by = models.ForeignKey["User | None", "User | None"](
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted",
    )

    # Use soft delete manager as default
    objects: ClassVar[models.Manager[Self]] = (  # ty:ignore[invalid-type-arguments]
        SoftDeleteManager()
    )
    # Manager to access all objects including deleted ones
    all_objects: ClassVar[models.Manager[Self]] = (  # ty:ignore[invalid-type-arguments]
        models.Manager()
    )

    class Meta:
        """Meta options for the model."""

        abstract = True


class SoftDeleteUserManager(UserManager["User"]):
    """User Manager that filters out soft-deleted objects by default."""

    @override
    def get_queryset(
        self,
    ) -> models.QuerySet["User"]:  # ty:ignore[invalid-type-arguments]
        """Return queryset excluding soft-deleted objects."""
        return super().get_queryset().filter(deleted=False)


class User(AbstractUser, BaseModel):
    """Custom User model extending Django's AbstractUser."""

    objects: ClassVar[UserManager["User"]] = SoftDeleteUserManager()


@final
class Author(BaseModel):
    """Model for a book author."""

    user = models.OneToOneField[User | None, User | None](
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    name = models.CharField[str, str](max_length=100)
    birth_date = models.DateField[date | None, date | None](null=True, blank=True)

    books: ClassVar[models.Manager["Book"]]  # Type hinting reverse relation

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "authors"

    @override
    def __str__(self) -> str:
        """Return the string representation of the author."""
        return str(self.name)

    @property
    def age(self) -> int:
        """Calculate the age of the author."""
        if self.birth_date is None:
            return 0

        today = datetime.now(tz=UTC).date()
        return int((today - self.birth_date).days / 365.25)

    @property
    def books_count(self) -> int:
        """Return the count of books written by the author."""
        return self.books.count()


@final
class AmazonAuthorProfile(BaseModel):
    """Model for an Amazon author profile."""

    author = models.OneToOneField[Author | None, Author | None](
        Author,
        on_delete=models.CASCADE,
        related_name="amazon_author_profile",
        blank=True,
        null=True,
    )
    profile_url = models.URLField[str | None, str | None](
        null=True, blank=True, max_length=200
    )
    description = models.TextField[str, str]()

    @override
    def __str__(self) -> str:
        """Return the string representation of the author profile."""
        author_name = self.author.name if self.author else "No author"
        return f"{author_name}: {self.description}"


@final
class PublisherWebsite(BaseModel):
    """Model for a website."""

    url = models.URLField[str, str](max_length=200)
    publisher = models.ForeignKey["Publisher", "Publisher"](
        "app.Publisher", on_delete=models.CASCADE
    )

    @final
    class Meta:
        default_related_name = "websites"


@final
class Publisher(BaseModel):
    """Model for a book publisher."""

    name = models.CharField[str, str](max_length=100)
    address = models.TextField[str, str](help_text="Publisher's official address")
    # CharField with choices for publisher type

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "publishers"

    @override
    def __str__(self) -> str:
        """Return the string representation of the publisher."""
        return str(self.name)

    @property
    def website(self) -> HttpUrl | None:
        """Return the latest website URL of the publisher."""
        latest_website = (
            PublisherWebsite.objects.filter(publisher=self).order_by("-id").first()
        )
        return HttpUrl(latest_website.url) if latest_website else None

    @website.setter
    def website(self, url: HttpUrl | None) -> None:
        if not url:
            return
        PublisherWebsite.objects.create(publisher=self, url=str(url))


def default_contact_user() -> User:
    """Return the user that represents the default contact."""
    return User.objects.get_or_create(
        username="default_contact", defaults={"email": "ceo@earth.com"}
    )[0]


def deleted_user() -> User:
    """Return dummy user that represents a deleted user."""
    return User.objects.get_or_create(username="deleted")[0]


@final
class ContactPerson(BaseModel):
    """Model for a contact person associated with a publisher."""

    publisher = models.ForeignKey[Publisher | None, Publisher | None](
        Publisher,
        on_delete=models.SET_NULL,  # Set to NULL on publisher deletion
        null=True,
        blank=True,
    )
    user = models.ForeignKey[User, User](
        User,
        on_delete=models.SET_DEFAULT,
        default=default_contact_user,
    )
    assistant = models.ForeignKey[User | None, User | None](
        User,
        on_delete=models.SET(deleted_user),
        null=True,
        blank=True,
        related_name="assistant_contacts",
    )

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "contacts"

    @override
    def __str__(self) -> str:
        """Return the string representation of the publisher contact."""
        publisher_name = self.publisher.name if self.publisher else "No Publisher"
        contact_name = cast("str", self.user.username)
        if self.assistant:
            contact_name += f" (Assistant: {cast('str', self.assistant.username)})"
        return f"{contact_name} - ({publisher_name})"


@final
class Book(BaseModel):
    """Model for a book."""

    title = models.CharField[str, str](max_length=200)
    isbn = models.CharField[str, str](max_length=13, unique=True)
    publication_date = models.DateField[date, date]()
    authors: models.ManyToManyField[Author, models.Model] = models.ManyToManyField(
        Author,
        blank=False,
    )  # Many-to-Many relationship with 'auto_created' through table
    favorite_users: models.ManyToManyField[User, models.Model] = models.ManyToManyField(
        User,
        blank=True,
        through="app.UserFavoriteBook",
        through_fields=("book", "user"),
        help_text="Users who have marked this book as a favorite",
    )  # Many-to-Many relationship with custom through model which supports soft delete
    publisher = models.ForeignKey[Publisher, Publisher](
        Publisher,
        on_delete=models.CASCADE,
    )  # Foreign Key relationship

    book_copies: ClassVar[models.Manager["BookCopy"]]  # Type hinting reverse relation

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "books"

    @override
    def __str__(self) -> str:
        """Return the string representation of the book."""
        return str(self.title)

    @property
    def authors_count(self) -> int:
        """Return the count of authors of the book."""
        return self.authors.count()

    @property
    def favorite_users_count(self) -> int:
        """Return the count of users who favorited this book."""
        return self.favorite_users.count()

    @property
    def book_copies_count(self) -> int:
        """Return the count of book copies of the book."""
        return self.book_copies.count()


@final
class UserFavoriteBook(BaseModel):
    """Through model for user favorite books relationship.

    This through model is based-off BaseModel which supports soft delete.
    """

    user = models.ForeignKey[User, User](
        User,
        on_delete=models.CASCADE,
        related_name="favorite_book_relations",
    )
    book = models.ForeignKey[Book, Book](
        Book,
        on_delete=models.CASCADE,
        related_name="favorite_user_relations",
    )

    @final
    class Meta:
        """Meta options for the model."""

        unique_together = ("user", "book")
        default_related_name = "user_favorite_books"
        verbose_name = "User Favorite Book"
        verbose_name_plural = "User Favorite Books"

    @override
    def __str__(self) -> str:
        """Return the string representation."""
        username = self.user.username  # pyright: ignore[reportUnknownMemberType]
        book_title = self.book.title
        return f"{username} favorited '{book_title}'"


@final
class Library(BaseModel):
    """Model for a library."""

    name = models.CharField[str, str](max_length=100)
    address = models.TextField[str, str]()

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "libraries"

    @override
    def __str__(self) -> str:
        """Return the string representation of the library."""
        return str(self.name)


@final
class BookCopy(BaseModel):
    """Model for a book copy."""

    book = models.ForeignKey[Book, Book](
        Book, on_delete=models.PROTECT
    )  # Foreign Key relationship that PROTECTs deletion if referenced
    library = models.ForeignKey[Library | None, Library | None](
        Library,
        on_delete=models.CASCADE,
        limit_choices_to={"name__icontains": "library"},
        null=True,
        blank=True,
    )  # Foreign Key relationship
    inventory_number = models.CharField[str, str](max_length=20, unique=True)

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "book_copies"

    @override
    def __str__(self) -> str:
        """Return the string representation of the book copy."""
        return f"{self.book.title} ({self.inventory_number})"


@final
class Borrowing(BaseModel):
    """Model for a borrowing."""

    user = models.ForeignKey[User, User](
        User, on_delete=models.CASCADE, related_name="user_borrowings"
    )  # Foreign Key relationship
    library = models.ForeignKey[Library, Library](
        Library, on_delete=models.CASCADE
    )  # Foreign Key relationship
    book_copy = models.ForeignKey[BookCopy, BookCopy](
        BookCopy,
        on_delete=models.RESTRICT,
    )  # Foreign Key relationship that RESTRICTs deletion if referenced
    borrow_date = models.DateField[date, date]()
    return_date = models.DateField[date | None, date | None](null=True, blank=True)

    @final
    class Meta:
        """Meta options for the model."""

        default_related_name = "borrowings"

    @override
    def __str__(self) -> str:
        """Return the string representation of the borrowing."""
        username = self.user.username  # pyright: ignore[reportUnknownMemberType]
        book_title = self.book_copy.book.title
        return f"{username} borrowed {book_title}"
