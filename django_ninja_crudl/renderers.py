"""Django Ninja CRUDL JSON Renderer."""

import json
from enum import Enum
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Any, override

from django.core.serializers.json import DjangoJSONEncoder
from ninja.renderers import JSONRenderer
from pydantic import BaseModel
from pydantic.networks import AnyUrl
from pydantic_core import Url

__all__ = ["CrudlJSONEncoder", "CrudlJSONRenderer"]


class CrudlJSONEncoder(DjangoJSONEncoder):
    """Custom JSON encoder for Django Ninja CRUDL."""

    @override
    def default(self, o: Any) -> Any:  # pyright: ignore [reportExplicitAny, reportAny]
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, (Url, AnyUrl)):
            return str(o)
        if isinstance(o, (IPv4Address, IPv4Network, IPv6Address, IPv6Network)):
            return str(o)
        if isinstance(o, Enum):
            return str(o)
        return super().default(o)  # pyright: ignore [reportAny]


class CrudlJSONRenderer(JSONRenderer):
    """Custom JSON renderer for Django Ninja CRUDL."""

    encoder_class: type[json.JSONEncoder] = CrudlJSONEncoder
