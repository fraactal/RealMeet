from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.calendars.contracts import ExternalCalendarProviderClient
from app.calendars.providers.fake import FakeExternalCalendarProvider
from app.calendars.providers.google import GoogleExternalCalendarProvider
from app.integrations.google_calendar import GoogleCalendarClient
from app.integrations.google_oauth import GoogleOAuthService
from app.models.external_calendar import ExternalCalendarProvider


class ExternalCalendarProviderRegistry:
    def __init__(self, db: Session | None = None, *, google_calendar_client: GoogleCalendarClient | None = None) -> None:
        self.db = db
        self.google_calendar_client = google_calendar_client

    def resolve(self, provider: ExternalCalendarProvider, *, integration_id: int | None = None, simulate_error: bool = False) -> ExternalCalendarProviderClient:
        if provider == ExternalCalendarProvider.fake:
            return FakeExternalCalendarProvider(simulate_error=simulate_error)
        if provider == ExternalCalendarProvider.google_calendar:
            if not self.db or not integration_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Calendar requires a connected integration")
            return GoogleExternalCalendarProvider(
                integration_id=integration_id,
                oauth_service=GoogleOAuthService(self.db),
                calendar_client=self.google_calendar_client,
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Calendar provider is not implemented yet")
