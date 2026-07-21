import json
import logging
import os
import re
import sys
from typing import Any


SENSITIVE_KEYS = ("password", "token", "secret", "authorization", "credential", "signature", "cookie")
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)(authorization[=:]\s*)(?:bearer\s+)?[^\s,;]+"),
    re.compile(r"(?i)(x-(?:hub-)?signature(?:-256)?[=:]\s*)[^\s,;]+"),
    re.compile(r"(?i)((?:password|token|secret|credential|api[_-]?key|client[_-]?secret)[=:]\s*)[^\s,;]+"),
)
_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_text(record.getMessage()),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(_redact(payload), ensure_ascii=False)


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper().strip()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_VALUE_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[redacted]", redacted)
    return redacted
