from datetime import datetime

from app.meetings.base import MeetingPayload, MeetingProvider


class MockMeetingProvider(MeetingProvider):
    def create_meeting(self, professional_name: str, starts_at: datetime) -> MeetingPayload:
        slug = professional_name.lower().replace(" ", "-")
        token = starts_at.strftime("%Y%m%d%H%M")
        return MeetingPayload(
            provider="mock",
            url=f"https://meet.realmeet.local/{slug}/{token}",
            external_id=f"mock-{token}",
            calendar_event_id=f"calendar-{token}",
        )
