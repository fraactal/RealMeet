from app.core.config import settings
from app.meetings.base import MeetingProvider
from app.meetings.mock import MockMeetingProvider


def get_meeting_provider() -> MeetingProvider:
    if settings.default_meeting_provider == "mock":
        return MockMeetingProvider()
    return MockMeetingProvider()
