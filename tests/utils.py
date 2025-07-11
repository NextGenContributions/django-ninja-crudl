"""Utility functions for testing."""

import json
import sys
from pathlib import Path
from typing import Any, override

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


class IntegerKeyJSONDecoder(json.JSONDecoder):
    """JSON decoder that converts positive integer string keys to integers."""

    @override
    def decode(self, s: str, **kwargs: Any) -> Any:  # type: ignore[override]  # pylint: disable=arguments-differ
        """Decode JSON string with integer key conversion."""
        obj = super().decode(s, **kwargs)  # pyright: ignore [reportAny]
        return self._convert_int_keys(obj)  # pyright: ignore [reportAny]

    def _convert_int_keys(self, obj: Any) -> Any:  # pyright: ignore [reportAny, reportExplicitAny]
        """Recursively convert string keys that represent positive integers to int."""
        if isinstance(obj, dict):
            return {
                self._convert_key(k): self._convert_int_keys(v) for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._convert_int_keys(item) for item in obj]
        return obj  # pyright: ignore [reportAny]

    @staticmethod
    def _convert_key(key: Any) -> int | Any:  # pyright: ignore [reportAny, reportExplicitAny]
        """Convert a key to an integer if it represents a positive integer."""
        if isinstance(key, str) and key.isdigit():
            return int(key)
        return key


def normalize_http_status_descriptions(data: Any) -> Any:  # pyright: ignore [reportAny, reportExplicitAny]  # noqa: ANN401
    """Normalize HTTP status descriptions for Python 3.12 and 3.13 compatibility.

    See diff for 422:
    - https://docs.python.org/3.12/library/http.html#http-status-codes
    - https://docs.python.org/3.13/library/http.html#http-status-codes
    """
    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            if key == "description" and value in (
                "Unprocessable Entity",
                "Unprocessable Content",
            ):
                # Use the correct description for the current Python version
                if sys.version_info >= (3, 13):
                    normalized[key] = "Unprocessable Content"
                else:
                    normalized[key] = "Unprocessable Entity"
            else:
                normalized[key] = normalize_http_status_descriptions(value)
        return normalized
    if isinstance(data, list):
        return [normalize_http_status_descriptions(item) for item in data]
    return data
