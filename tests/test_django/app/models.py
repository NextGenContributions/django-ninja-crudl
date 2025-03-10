"""Models for the Django test project."""

from typing import override

from django.contrib.auth.models import User
from django.db import models


class Author(models.Model):
    """Model for a book author."""

    id: int  # Just for type hinting

    name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)

    books: models.Manager["Book"]

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
        import datetime

        return int((datetime.date.today() - self.birth_date).days / 365.25)

    @property
    def books_count(self) -> int:
        """Return the count of books written by the author."""
        return self.books.count()


class Publisher(models.Model):
    """Model for a book publisher."""

    id: int  # Just for type hinting

    name = models.CharField(max_length=100)
    address = models.TextField(help_text="Publisher's official address")

    class Meta:
        """Meta options for the model."""

        default_related_name = "publishers"

    @override
    def __str__(self) -> str:
        """Return the string representation of the publisher."""
        return str(self.name)


class Book(models.Model):
    """Model for a book."""

    id: int  # Just for type hinting

    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    publication_date = models.DateField()
    authors: models.ManyToManyField[Author, models.Model] = models.ManyToManyField(
        Author,
        blank=False,
    )  # Many-to-Many relationship
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
    )  # Foreign Key relationship

    book_copies: models.Manager["BookCopy"]

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
    def book_copies_count(self) -> int:
        """Return the count of book copies of the book."""
        return self.book_copies.count()


class Library(models.Model):
    """Model for a library."""

    name = models.CharField(max_length=100)
    address = models.TextField()

    class Meta:
        """Meta options for the model."""

        default_related_name = "libraries"

    @override
    def __str__(self) -> str:
        """Return the string representation of the library."""
        return str(self.name)


class BookCopy(models.Model):
    """Model for a book copy."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE)  # Foreign Key relationship
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
    )  # Foreign Key relationship
    inventory_number = models.CharField(max_length=20, unique=True)

    class Meta:
        """Meta options for the model."""

        default_related_name = "book_copies"

    @override
    def __str__(self) -> str:
        """Return the string representation of the book copy."""
        return f"{self.book.title} ({self.inventory_number})"


class Borrowing(models.Model):
    """Model for a borrowing."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Foreign Key relationship
    book_copy = models.ForeignKey(
        BookCopy,
        on_delete=models.CASCADE,
    )  # Foreign Key relationship
    borrow_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    class Meta:
        """Meta options for the model."""

        default_related_name = "borrowings"

    @override
    def __str__(self) -> str:
        """Return the string representation of the borrowing."""
        return f"{self.user.username} borrowed {self.book_copy.book.title}"
