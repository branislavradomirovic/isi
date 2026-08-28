import pytest

from src.platform.ai.structured import StructuredOutputError, parse_structured_output


SCHEMA = {
    "type": "object",
    "required": ["status", "message"],
    "properties": {
        "status": {"type": "string", "enum": ["ok"]},
        "message": {"type": "string"},
    },
}


def test_valid_structured_output():
    assert parse_structured_output('{"status":"ok","message":"pass"}', SCHEMA)["status"] == "ok"


def test_invalid_json_is_rejected():
    with pytest.raises(StructuredOutputError, match="invalid_json"):
        parse_structured_output("not-json", SCHEMA)


def test_missing_required_field_is_rejected():
    with pytest.raises(StructuredOutputError, match="missing_required:message"):
        parse_structured_output('{"status":"ok"}', SCHEMA)
