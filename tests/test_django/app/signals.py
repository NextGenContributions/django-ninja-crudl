# flake8: noqa: ARG001, FBT001, ANN401, D100, D103
# pyright: reportUnusedParameter=false, reportExplicitAny=false, reportAny=false
from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from tests.test_django.app.models import Publisher


def pre_save_publisher_mock() -> None: ...
def post_save_publisher_mock() -> None: ...


@receiver(pre_save, sender=Publisher)
def pre_save_publisher(
    sender: type[Publisher],
    instance: Publisher,
    **kwargs: Any,
) -> None:
    pre_save_publisher_mock()


@receiver(post_save, sender=Publisher)
def post_save_publisher(
    sender: type[Publisher],
    instance: Publisher,
    created: bool,
    **kwargs: Any,
) -> None:
    post_save_publisher_mock()
