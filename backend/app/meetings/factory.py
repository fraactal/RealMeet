from app.core.config import settings
from app.meetings.base import MeetingProvider
from app.meetings.google_meet import GoogleMeetProvider
from app.meetings.mock import MockMeetingProvider
from app.meetings.zoom import ZoomProvider


def get_meeting_provider() -> MeetingProvider:
    if settings.default_meeting_provider == "mock":
        return MockMeetingProvider(settings.mock_meeting_base_url)
    if settings.default_meeting_provider == "google_meet":
        return GoogleMeetProvider()
    if settings.default_meeting_provider == "zoom":
        return ZoomProvider()
    raise RuntimeError("Unsupported meeting provider")
