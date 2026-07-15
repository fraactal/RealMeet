import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.integrations.exceptions import IntegrationValidationError

SECRET_REFERENCE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")

SENSITIVE_KEY_PARTS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "credential",
    "credentials",
    "private_key",
}


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


NORMALIZED_SENSITIVE_KEYS = {normalize_key(item) for item in SENSITIVE_KEY_PARTS}


def validate_secret_reference(secret_reference: str | None) -> str | None:
    if secret_reference is None:
        return None
    if not SECRET_REFERENCE_PATTERN.fullmatch(secret_reference):
        raise IntegrationValidationError("secret_reference must be an uppercase environment variable reference")
    return secret_reference


def validate_safe_metadata(value: Any, *, field_name: str, max_depth: int = 8) -> Any:
    _validate_safe_value(value, field_name=field_name, path=field_name, depth=0, max_depth=max_depth)
    return value


def _validate_safe_value(value: Any, *, field_name: str, path: str, depth: int, max_depth: int) -> None:
    if depth > max_depth:
        raise IntegrationValidationError(f"{field_name} exceeds the maximum allowed nesting depth")

    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise IntegrationValidationError(f"{field_name} keys must be strings")
            normalized_key = normalize_key(key)
            if normalized_key in NORMALIZED_SENSITIVE_KEYS:
                raise IntegrationValidationError(f"{field_name} contains a sensitive key: {path}.{key}")
            _validate_safe_value(nested_value, field_name=field_name, path=f"{path}.{key}", depth=depth + 1, max_depth=max_depth)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_safe_value(item, field_name=field_name, path=f"{path}[{index}]", depth=depth + 1, max_depth=max_depth)
