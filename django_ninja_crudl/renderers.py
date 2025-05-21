import json
from enum import Enum
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Any, override

from django.core.serializers.json import DjangoJSONEncoder
from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder
from pydantic import BaseModel
from pydantic.networks import AnyUrl
from pydantic_core import Url

__all__ = ["CrudlJSONRenderer", "NinjaJSONEncoder"]


class CrudlJSONEncoder(DjangoJSONEncoder):
    @override
    def default(self, o: Any) -> Any:  # pyright: ignore [reportExplicitAny, reportAny]
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, Url):
            return str(o)
        if isinstance(o, AnyUrl):
            return str(o)
        if isinstance(o, (IPv4Address, IPv4Network, IPv6Address, IPv6Network)):
            return str(o)
        if isinstance(o, Enum):
            return str(o)
        return super().default(o)  # pyright: ignore [reportAny]


class CrudlJSONRenderer(JSONRenderer):
    encoder_class: type[json.JSONEncoder] = CrudlJSONEncoder
