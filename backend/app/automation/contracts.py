from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.automation.enums import WebhookEventType


EVENT_VERSION = 1


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: WebhookEventType
    event_version: int
    occurred_at: datetime
    entity_type: str
    entity_id: str
    correlation_id: str
    payload: dict[str, Any]

    @classmethod
    def create(
        cls,
        *,
        event_type: WebhookEventType,
        entity_type: str,
        entity_id: str | int,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> "DomainEvent":
        generated_id = f"{event_type.value}:{entity_id}:{uuid4().hex}"
        return cls(
            event_id=generated_id,
            event_type=event_type,
            event_version=EVENT_VERSION,
            occurred_at=datetime.now(UTC),
            entity_type=entity_type,
            entity_id=str(entity_id),
            correlation_id=correlation_id or generated_id,
            payload=payload,
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "source": "realmeet",
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "correlation_id": self.correlation_id,
            "payload": self.payload,
        }
