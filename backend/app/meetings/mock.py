import hashlib
from datetime import UTC, datetime

from app.meetings.base import MeetingPayload, MeetingProvider


class MockMeetingProvider(MeetingProvider):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "mock"

    def create_meeting(self, professional_name: str, starts_at: datetime) -> MeetingPayload:
        source = f"{professional_name.strip().lower()}|{starts_at.isoformat()}".encode()
        token = hashlib.sha256(source).hexdigest()[:16]
        return MeetingPayload(
            provider="mock",
            url=f"{self.base_url}/{token}",
            external_id=f"mock-{token}",
            calendar_event_id=f"calendar-{token}",
            status="active",
            created_at=datetime.now(UTC),
        )
