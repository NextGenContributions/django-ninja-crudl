"""CRUDL API base class."""

import logging
from abc import ABC, ABCMeta
from typing import Generic, TypeGuard, cast

from beartype import beartype
from django.db.models import Model
from ninja_extra import (
    ControllerBase,
    api_controller,  # pyright: ignore[reportUnknownVariableType]
)

from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.config import CrudlConfig
from django_ninja_crudl.endpoints import (
    get_create_endpoint,
    get_delete_endpoint,
    get_get_many_endpoint,
    get_get_one_endpoint,
    get_partial_update_endpoint,
    get_update_endpoint,
)
from django_ninja_crudl.types import DictStrAny, TDjangoModel

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


class CrudlMeta(ABCMeta):
    """Metaclass for the CRUDL API."""

    def __new__(  # noqa: C901,WPS210
        mcs,  # noqa: N804
        name: str,
        bases: tuple[type[object], ...],
        dct: DictStrAny,
    ) -> "type[ControllerBase] | CrudlMeta":
        """Create a new class."""
        # Quit if this is an abstract base class
        if not dct.get("config") or name == "CrudlController":
            return super().__new__(mcs, name, bases, dct)

        config = dct.get("config")

        if not config or not mcs.is_crudl_config(config):  # pyright: ignore[reportAny]
            class_name = __name__
            config_module = f"{CrudlConfig.__module__}.{CrudlConfig.__qualname__}"
            msg = (
                f"Class '{class_name}' must have a 'config' attribute, "
                f" which must be an instance or subclass of {config_module}."
            )
            raise ValueError(msg)

        endpoints: list[type] = []
        if config.create_schema:
            create_endpoint = get_create_endpoint(config)
            endpoints.append(create_endpoint)
        if config.get_one_schema:
            get_one_endpoint = get_get_one_endpoint(config)
            endpoints.append(get_one_endpoint)
        if config.list_schema:
            list_endpoint = get_get_many_endpoint(config)
            endpoints.append(list_endpoint)
        if config.update_schema:
            update_endpoint = get_update_endpoint(config)
            endpoints.append(update_endpoint)
        if config.partial_update_schema:
            partial_update_endpoint = get_partial_update_endpoint(config)
            endpoints.append(partial_update_endpoint)
        if config.delete_allowed:
            delete_endpoint = get_delete_endpoint(config)
            endpoints.append(delete_endpoint)

        # Add (overwrite if necessary) all mro attributes to the controller class
        # This allows the controller class to inherit all attributes from
        # parent class of the `Crudl` class.
        bases_dct = {
            attr_name: attr_value
            for base in bases
            for attr_name, attr_value in base.__dict__.items()  # pyright: ignore[reportAny]
            if not attr_name.startswith("__")
        }

        # Add all attributes to dct, while allowing the child's attributes to overwrite
        # parents' attributes
        dct = bases_dct | dct

        # Construct the final API controller class
        bases = (ControllerBase, CrudlBaseMethodsMixin)
        final_bases = tuple(endpoints) + bases
        return cast(
            type[ControllerBase],
            api_controller(tags=config.tags)(
                type(
                    name,
                    final_bases,
                    dct,
                )
            ),
        )

    @classmethod
    def is_crudl_config(mcs, obj: object) -> TypeGuard[CrudlConfig[Model]]:  # noqa: N804
        """Check if the object is an instance of the class."""
        return isinstance(obj, CrudlConfig)


@beartype
class CrudlController(  # noqa: WPS215
    Generic[TDjangoModel],
    CrudlBaseMethodsMixin[TDjangoModel],
    ControllerBase,
    ABC,
    metaclass=CrudlMeta,
):
    """Controller for CRUDL operations."""

    config: CrudlConfig[TDjangoModel]
