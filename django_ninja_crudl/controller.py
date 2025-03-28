"""CRUDL API base class."""

import logging
from abc import ABCMeta

from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneRel,
)
from ninja_extra import ControllerBase, api_controller
from ninja_extra.main import APIController

from django_ninja_crudl import CrudlConfig
from django_ninja_crudl.base import CrudlBaseMethodsMixin
from django_ninja_crudl.endpoints.create import get_create_endpoint
from django_ninja_crudl.endpoints.delete import get_delete_endpoint
from django_ninja_crudl.endpoints.get_one import get_get_one_endpoint
from django_ninja_crudl.endpoints.list import get_get_many_endpoint
from django_ninja_crudl.endpoints.partial_update import get_partial_update_endpoint
from django_ninja_crudl.endpoints.update import get_update_endpoint
from django_ninja_crudl.types import JSON, DictStrAny

logger: logging.Logger = logging.getLogger("django_ninja_crudl")


DjangoRelationFields = (
    ManyToManyField[Model, Model] | ManyToManyRel | ManyToOneRel | OneToOneRel
)


class CrudlMeta(ABCMeta):
    """Metaclass for the CRUDL API."""

    def __new__(
        cls, name: str, bases: tuple[type[object], ...], dct: DictStrAny
    ) -> type[object]:
        """Create a new class."""
        # quit if this is an abstract base class
        if not dct.get("config") or name == "CrudlController":
            return super().__new__(cls, name, bases, dct)

        config = dct.get("config")

        if not config or not isinstance(config, CrudlConfig):
            class_name = __name__
            config_module = f"{CrudlConfig.__module__}.{CrudlConfig.__qualname__}"
            msg = (
                f"Class '{class_name}' must have a 'config' attribute, "
                f" which must be an instance or subclass of {config_module}."
            )
            raise ValueError(msg)

        endpoints = ()

        if config.create_schema:
            create_endpoint = get_create_endpoint(config)
            endpoints += (create_endpoint,)
        if config.get_one_schema:
            get_one_endpoint = get_get_one_endpoint(config)
            endpoints += (get_one_endpoint,)
        if config.list_schema:
            list_endpoint = get_get_many_endpoint(config)
            endpoints += (list_endpoint,)
        if config.update_schema:
            update_endpoint = get_update_endpoint(config)
            endpoints += (update_endpoint,)
        if config.partial_update_schema:
            partial_update_endpoint = get_partial_update_endpoint(config)
            endpoints += (partial_update_endpoint,)
        if config.delete_allowed:
            delete_endpoint = get_delete_endpoint(config)
            endpoints += (delete_endpoint,)

        # Add (overwrite if necessary) all mro attributes to the controller class
        # This allows the controller class to inherit all attributes from
        # parent class of the `Crudl` class.
        bases_dct = {}
        for base in bases:
            for attr_name, attr_value in base.__dict__.items():
                if not attr_name.startswith("__"):
                    bases_dct[attr_name] = attr_value

        # Add all attributes to dct, while allowing the child's attributes to overwrite
        # parents' attributes
        for attr_name, attr_value in bases_dct.items():
            dct = bases_dct | dct

        # Contruct the final API controller class
        # bases = (APIController, ControllerBase, CrudlBaseMethodsMixin)
        # TODO(phuongfi91): ^ why did we have APIController here?
        bases = (ControllerBase, CrudlBaseMethodsMixin)
        final_bases = endpoints + bases
        dynamic_class = api_controller(tags=config.tags)(
            type(
                name,
                final_bases,
                dct,
            )
        )
        return dynamic_class
