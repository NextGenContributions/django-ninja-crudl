"""Pytest configuration file."""

import os

import django_stubs_ext
from django import setup

django_stubs_ext.monkeypatch()


def pytest_configure(config) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_django.settings")

    # Setup Django
    setup()
