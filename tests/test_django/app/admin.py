"""Admin configuration for the test app."""

from django.contrib import admin

from tests.test_django.app import models


@admin.register(models.Author)
class AuthorAdmin(admin.ModelAdmin[models.Author]):
    """Admin configuration for the Author model."""


@admin.register(models.Publisher)
class PublisherAdmin(admin.ModelAdmin[models.Publisher]):
    """Admin configuration for the Publisher model."""


@admin.register(models.Book)
class BookAdmin(admin.ModelAdmin[models.Book]):
    """Admin configuration for the Book model."""
