"""JSON Schema validation helper for API responses."""
from __future__ import annotations

from typing import Any, Dict

import jsonschema
from jsonschema import Draft7Validator

from utils.logger import get_logger

log = get_logger("schema_validator")


def validate_schema(instance: Any, schema: Dict[str, Any]) -> None:
    """Validate ``instance`` against a JSON Schema, raising on failure.

    Aggregates all validation errors into a single readable assertion message.
    """
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        messages = "; ".join(
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in errors
        )
        raise AssertionError(f"JSON schema validation failed: {messages}")
    log.debug("JSON schema validation passed")


def is_valid(instance: Any, schema: Dict[str, Any]) -> bool:
    try:
        jsonschema.validate(instance=instance, schema=schema)
        return True
    except jsonschema.ValidationError:
        return False
