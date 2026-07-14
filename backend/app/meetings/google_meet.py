from datetime import datetime

from app.meetings.base import MeetingPayload, MeetingProvider


class GoogleMeetProvider(MeetingProvider):
    def create_meeting(self, professional_name: str, starts_at: datetime) -> MeetingPayload:
        raise NotImplementedError("Google Meet integration is not enabled in MVP phase")
