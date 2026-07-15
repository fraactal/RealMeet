from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MeetingAttendee:
    email: str


@dataclass(frozen=True)
class MeetingCreateRequest:
    title: str
    start_at: datetime
    end_at: datetime
    timezone: str
    idempotency_key: str
    description: str = "Reunion programada mediante RealMeet."
    attendees: list[MeetingAttendee] = field(default_factory=list)
    send_updates: str = "none"
    external_reference: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None


@dataclass
class MeetingResult:
    provider: str
    external_event_id: str
    external_calendar_id: str
    meeting_url: str | None
    html_link: str | None
    conference_id: str | None
    status: str
    start_at: datetime
    end_at: datetime
    created_at: datetime | None = None
    metadata: dict | None = None
