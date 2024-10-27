"""Utility functions for testing."""

import json
from pathlib import Path
from typing import Any

from django.db import models
from rich import print_json

DjangoField = models.Field[Any, Any]

JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]


def debug_json(json_data: JSONValue) -> None:  # pragma: no cover
    """Print pretty the JSON value with indentation."""
    json_str: str = json.dumps(json_data)
    print_json(data=json_str, indent=4)
    with Path("debug.json").open("w") as file:
        file.write(json_str)
