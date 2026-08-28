from __future__ import annotations

import json
from typing import Any


class StructuredOutputError(ValueError):
    pass


_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def parse_structured_output(text: str, schema: dict[str, Any] | None) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError("invalid_json") from exc
    if not isinstance(value, dict):
        raise StructuredOutputError("structured_output_must_be_object")
    if not schema:
        return value
    if schema.get("type", "object") != "object":
        raise StructuredOutputError("unsupported_schema_root")
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise StructuredOutputError("invalid_schema_required")
    for key in required:
        if key not in value:
            raise StructuredOutputError(f"missing_required:{key}")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise StructuredOutputError("invalid_schema_properties")
    for key, rule in properties.items():
        if key not in value or not isinstance(rule, dict):
            continue
        expected = rule.get("type")
        if expected:
            pytype = _TYPE_MAP.get(expected)
            if pytype is None:
                raise StructuredOutputError(f"unsupported_property_type:{expected}")
            actual = value[key]
            if expected in {"integer", "number"} and isinstance(actual, bool):
                raise StructuredOutputError(f"invalid_type:{key}")
            if not isinstance(actual, pytype):
                raise StructuredOutputError(f"invalid_type:{key}")
        if "enum" in rule and value[key] not in rule["enum"]:
            raise StructuredOutputError(f"invalid_enum:{key}")
    return value
