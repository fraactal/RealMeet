from fastapi import HTTPException, status

from app.calendars.contracts import ExternalCalendarProviderClient
from app.calendars.providers.fake import FakeExternalCalendarProvider
from app.models.external_calendar import ExternalCalendarProvider


class ExternalCalendarProviderRegistry:
    def resolve(self, provider: ExternalCalendarProvider, *, simulate_error: bool = False) -> ExternalCalendarProviderClient:
        if provider == ExternalCalendarProvider.fake:
            return FakeExternalCalendarProvider(simulate_error=simulate_error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Calendar provider is not implemented yet")
