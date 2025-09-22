"""App config."""
from typing import override

from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    """App config."""

    name = "tests.test_django.app"
    verbose_name = "App"

    @override
    def ready(self) -> None:
        from . import signals  # noqa: F401, PLC0415
