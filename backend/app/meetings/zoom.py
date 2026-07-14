from datetime import datetime

from app.meetings.base import MeetingPayload, MeetingProvider


class ZoomProvider(MeetingProvider):
    def create_meeting(self, professional_name: str, starts_at: datetime) -> MeetingPayload:
        raise NotImplementedError("Zoom integration is not enabled in MVP phase")
