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
from django_ninja_crudl.errors.openapi_extras import (
    not_authorized_openapi_extra,
    throttle_openapi_extra,
)
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
            print("No config", cls, name, bases, dct)
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

        bases = (APIController, ControllerBase, CrudlBaseMethodsMixin)
        final_bases = endpoints + bases

        print("final_bases", final_bases)

        dynamic_class = api_controller(tags=config.tags)(
            type(
                name,
                final_bases,
                dct,
            )
        )

        return dynamic_class

    # TODO(phuongfi91): use this where it needed
    @classmethod
    def _create_schema_extra(
        cls,
        get_one_operation_id: str,
        update_operation_id: str,
        partial_update_operation_id: str,
        delete_operation_id: str,
        create_response_name: str,
        resource_name: str,
    ) -> JSON:
        """Create the OpenAPI links for the create operation.

        Ref: https://swagger.io/docs/specification/v3_0/links/
        """
        res_body_id = "$response.body#/id"
        return {
            "responses": {
                201: {
                    "description": "Created",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"#/components/schemas/{create_response_name}",
                            },
                        },
                    },
                    "links": {
                        "UpdateById": {
                            "operationId": update_operation_id,
                            "parameters": {"id": res_body_id},
                            "description": f"Update {resource_name} by id",
                        },
                        "DeleteById": {
                            "operationId": delete_operation_id,
                            "parameters": {"id": res_body_id},
                            "description": f"Delete {resource_name} by id",
                        },
                        "GetById": {
                            "operationId": get_one_operation_id,
                            "parameters": {"id": res_body_id},
                            "description": f"Get {resource_name} by id",
                        },
                        "PatchById": {
                            "operationId": partial_update_operation_id,
                            "parameters": {"id": res_body_id},
                            "description": f"Patch {resource_name} by id",
                        },
                    },
                },
                **not_authorized_openapi_extra,
                **throttle_openapi_extra,
            },
        }
