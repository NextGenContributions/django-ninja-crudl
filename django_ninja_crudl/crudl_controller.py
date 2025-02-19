"""Shared types for the CRUDL classes."""

import abc
from typing import Generic, TypeGuard

from beartype import beartype

from django_ninja_crudl import ControllerBase
from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.config import CrudlConfig
from django_ninja_crudl.controller import CrudlMeta
from django_ninja_crudl.schema import Schema
from django_ninja_crudl.types import TDjangoModel_co


@beartype
class CrudlController(  # noqa: WPS215
    Generic[TDjangoModel_co],
    CrudlBaseMethodsMixin[TDjangoModel_co],
    ControllerBase,
    abc.ABC,
    metaclass=CrudlMeta,
):
    """Controller for CRUDL operations."""

    config: CrudlConfig[TDjangoModel_co]

    @beartype
    def __init__(self) -> None:
        """Initialize the CrudlController class."""
        # Basic validation
        if not self.is_crudl_config(self.config):
            class_name = self.__class__.__name__
            current_type = type(self.config)
            required_type = f"{CrudlConfig.__module__}.{CrudlConfig.__qualname__}"
            msg = (
                f"The `config` attribute of `{class_name}` must"
                f" be an instance of `{required_type}`, not `{current_type}`."
            )
            raise ValueError(msg)

        # If using django2pydantic.Schema, set the model attribute:
        if self.is_schema(self.config.create_schema):
            self.config.create_schema.Meta.model = self.config.model
        if self.is_schema(self.config.update_schema):
            self.config.update_schema.Meta.model = self.config.model
        if self.is_schema(self.config.get_one_schema):
            self.config.get_one_schema.Meta.model = self.config.model
        if self.is_schema(self.config.list_schema):
            self.config.list_schema.Meta.model = self.config.model

        super().__init__()

    def __getitem__(self, key: str) -> None:
        """Get the value of the key."""

    @staticmethod
    def is_crudl_config(obj: object) -> TypeGuard[CrudlConfig[TDjangoModel_co]]:
        """Check if the object is an instance of CrudlConfig."""
        return isinstance(obj, CrudlConfig)

    @staticmethod
    def is_schema(obj: object) -> TypeGuard[Schema[TDjangoModel_co]]:
        """Check if the object is an instance of Schema."""
        return isinstance(obj, Schema)
