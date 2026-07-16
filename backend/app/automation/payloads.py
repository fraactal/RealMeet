from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.automation.enums import WebhookEventType
from app.models.appointment import Appointment, AppointmentNotification


SCHEMA_VERSION = "1.0"
DEFAULT_TIMEZONE = "America/Santiago"


class StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AppointmentSummary(StrictPayload):
    id: int
    status: str
    starts_at: str
    ends_at: str | None = None
    timezone: str = DEFAULT_TIMEZONE


class PersonSummary(StrictPayload):
    id: int
    display_name: str
    email: str | None = None
    phone: str | None = None


class AppointmentCreatedAutomationPayload(StrictPayload):
    schema_version: str
    event_type: str
    event_id: str
    occurred_at: str
    appointment: AppointmentSummary
    professional: PersonSummary
    client: PersonSummary


class AppointmentCancelledAutomationPayload(AppointmentCreatedAutomationPayload):
    cancellation_reason: str | None = None


class MeetingReadyAutomationPayload(StrictPayload):
    schema_version: str
    event_type: str
    event_id: str
    occurred_at: str
    appointment: AppointmentSummary
    meeting: dict[str, str | bool | None]


class NotificationFailedAutomationPayload(StrictPayload):
    schema_version: str
    event_type: str
    event_id: str
    occurred_at: str
    notification: dict[str, str | int | None]


class AutomationPayloadBuilder:
    def build(self, event_type: WebhookEventType, resource: Any, *, event_id: str, occurred_at: datetime | None = None) -> dict[str, Any]:
        if event_type == WebhookEventType.appointment_created:
            return self.appointment_created(resource, event_id=event_id, occurred_at=occurred_at)
        if event_type == WebhookEventType.appointment_cancelled:
            return self.appointment_cancelled(resource, event_id=event_id, occurred_at=occurred_at)
        if event_type == WebhookEventType.meeting_ready:
            return self.meeting_ready(resource, event_id=event_id, occurred_at=occurred_at)
        if event_type == WebhookEventType.notification_failed:
            return self.notification_failed(resource, event_id=event_id, occurred_at=occurred_at)
        return {}

    def appointment_created(self, appointment: Appointment, *, event_id: str, occurred_at: datetime | None = None) -> dict[str, Any]:
        payload = AppointmentCreatedAutomationPayload(
            **self._base(WebhookEventType.appointment_created, event_id, occurred_at),
            appointment=self._appointment_summary(appointment),
            professional=self._professional_summary(appointment),
            client=self._client_summary(appointment),
        )
        return payload.model_dump(exclude_none=True)

    def appointment_cancelled(self, appointment: Appointment, *, event_id: str, occurred_at: datetime | None = None) -> dict[str, Any]:
        payload = AppointmentCancelledAutomationPayload(
            **self._base(WebhookEventType.appointment_cancelled, event_id, occurred_at),
            appointment=self._appointment_summary(appointment),
            professional=self._professional_summary(appointment),
            client=self._client_summary(appointment),
            cancellation_reason=self._safe_text(getattr(appointment, "cancellation_reason", None)),
        )
        return payload.model_dump(exclude_none=True)

    def meeting_ready(self, appointment: Appointment, *, event_id: str, occurred_at: datetime | None = None) -> dict[str, Any]:
        meeting = getattr(appointment, "meeting_link", None)
        payload = MeetingReadyAutomationPayload(
            **self._base(WebhookEventType.meeting_ready, event_id, occurred_at),
            appointment=self._appointment_summary(appointment),
            meeting={
                "provider": self._enum_value(getattr(meeting, "provider", getattr(appointment, "meeting_provider", None))),
                "status": self._enum_value(getattr(meeting, "status", None)) or "ready",
                "has_join_url": bool(getattr(meeting, "meeting_url", None) or getattr(appointment, "meeting_url", None)),
                "external_reference": self._safe_text(getattr(meeting, "external_reference", None)),
            },
        )
        return payload.model_dump(exclude_none=True)

    def notification_failed(self, notification: AppointmentNotification | Any, *, event_id: str, occurred_at: datetime | None = None) -> dict[str, Any]:
        payload = NotificationFailedAutomationPayload(
            **self._base(WebhookEventType.notification_failed, event_id, occurred_at),
            notification={
                "id": getattr(notification, "id", None),
                "channel": self._enum_value(getattr(notification, "channel", None)),
                "status": self._enum_value(getattr(notification, "status", None)) or "failed",
                "event_type": self._enum_value(getattr(notification, "event_type", None)),
                "appointment_id": getattr(notification, "appointment_id", None),
                "error_code": self._safe_text(getattr(notification, "error_code", None)),
            },
        )
        return payload.model_dump(exclude_none=True)

    def _base(self, event_type: WebhookEventType, event_id: str, occurred_at: datetime | None) -> dict[str, str]:
        timestamp = occurred_at or datetime.now(UTC)
        return {
            "schema_version": SCHEMA_VERSION,
            "event_type": event_type.value,
            "event_id": event_id,
            "occurred_at": timestamp.isoformat(),
        }

    def _appointment_summary(self, appointment: Appointment) -> AppointmentSummary:
        return AppointmentSummary(
            id=int(getattr(appointment, "id")),
            status=self._enum_value(getattr(appointment, "status", None)) or "unknown",
            starts_at=self._iso(getattr(appointment, "start_datetime", None)),
            ends_at=self._iso(getattr(appointment, "end_datetime", None)),
            timezone=DEFAULT_TIMEZONE,
        )

    def _professional_summary(self, appointment: Appointment) -> PersonSummary:
        profile = getattr(appointment, "professional", None)
        user = getattr(profile, "user", None)
        return PersonSummary(
            id=int(getattr(appointment, "professional_id", getattr(profile, "id", 0)) or 0),
            display_name=self._display_name(user, fallback="Profesional RealMeet"),
        )

    def _client_summary(self, appointment: Appointment) -> PersonSummary:
        profile = getattr(appointment, "client", None)
        user = getattr(profile, "user", None)
        return PersonSummary(
            id=int(getattr(appointment, "client_id", getattr(profile, "id", 0)) or 0),
            display_name=self._display_name(user, fallback="Cliente RealMeet"),
            email=self._safe_email(getattr(user, "email", None)),
            phone=mask_phone(getattr(user, "phone", None)),
        )

    @staticmethod
    def _display_name(user: Any, *, fallback: str) -> str:
        if not user:
            return fallback
        name = " ".join(part for part in [getattr(user, "first_name", ""), getattr(user, "last_name", "")] if part).strip()
        return name or fallback

    @staticmethod
    def _enum_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(getattr(value, "value", value))

    @staticmethod
    def _iso(value: Any) -> str | None:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value) if value else None

    @staticmethod
    def _safe_email(value: str | None) -> str | None:
        if not value:
            return None
        cleaned = value.strip()
        return cleaned if "@" in cleaned and len(cleaned) <= 255 else None

    @staticmethod
    def _safe_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text[:120] if text else None


def mask_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) < 4:
        return None
    prefix = "+" if value.strip().startswith("+") else ""
    country = digits[:3] if len(digits) > 8 else digits[:2]
    return f"{prefix}{country}{'*' * max(len(digits) - len(country) - 4, 4)}{digits[-4:]}"
