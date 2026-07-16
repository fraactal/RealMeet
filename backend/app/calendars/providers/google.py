from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status

from app.calendars.contracts import BusyPeriod, CalendarProviderHealth, ExternalCalendarEventInput, ExternalCalendarEventResult, ExternalCalendarInfo
from app.integrations.exceptions import IntegrationError
from app.integrations.google_calendar import GoogleCalendarClient, GoogleCalendarHTTPClient, _parse_datetime
from app.integrations.google_oauth import GoogleOAuthService


class GoogleExternalCalendarProvider:
    def __init__(
        self,
        *,
        integration_id: int,
        oauth_service: GoogleOAuthService,
        calendar_client: GoogleCalendarClient | None = None,
    ) -> None:
        self.integration_id = integration_id
        self.oauth_service = oauth_service
        self.calendar_client = calendar_client or GoogleCalendarHTTPClient()

    def list_calendars(self) -> list[ExternalCalendarInfo]:
        token = self._access_token()
        items = self.calendar_client.list_calendars(access_token=token)
        calendars: list[ExternalCalendarInfo] = []
        for item in items:
            access_role = item.get("accessRole") or "reader"
            calendars.append(
                ExternalCalendarInfo(
                    external_calendar_id=item["id"],
                    name=item.get("summary") or item["id"],
                    description=item.get("description"),
                    timezone=item.get("timeZone") or "UTC",
                    is_primary=bool(item.get("primary")),
                    read_only=access_role == "reader",
                )
            )
        return calendars

    def list_busy_periods(self, calendar_id: str, starts_at: datetime, ends_at: datetime) -> list[BusyPeriod]:
        token = self._access_token()
        data = self.calendar_client.freebusy(
            access_token=token,
            calendar_ids=[calendar_id],
            time_min=starts_at,
            time_max=ends_at,
            timezone="UTC",
        )
        calendar_data = (data.get("calendars") or {}).get(calendar_id) or {}
        if calendar_data.get("errors"):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Calendar no pudo consultar FreeBusy")
        return [
            BusyPeriod(
                starts_at=_parse_datetime(item["start"]),
                ends_at=_parse_datetime(item["end"]),
                source_calendar_id=calendar_id,
                external_event_id=None,
                availability="busy",
            )
            for item in calendar_data.get("busy") or []
        ]

    def create_event(self, payload: ExternalCalendarEventInput) -> ExternalCalendarEventResult:
        token = self._access_token()
        result = self.calendar_client.create_plain_event(access_token=token, calendar_id=payload.calendar_id, payload=payload, send_updates="none")
        return ExternalCalendarEventResult(result.event_id, payload.calendar_id, "created")

    def update_event(self, external_event_id: str, payload: ExternalCalendarEventInput) -> ExternalCalendarEventResult:
        token = self._access_token()
        result = self.calendar_client.update_plain_event(access_token=token, calendar_id=payload.calendar_id, event_id=external_event_id, payload=payload, send_updates="none")
        return ExternalCalendarEventResult(result.event_id, payload.calendar_id, "updated")

    def delete_event(self, calendar_id: str, external_event_id: str) -> ExternalCalendarEventResult:
        token = self._access_token()
        self.calendar_client.delete_event(access_token=token, calendar_id=calendar_id, event_id=external_event_id, send_updates="none")
        return ExternalCalendarEventResult(external_event_id, calendar_id, "cancelled")

    def get_event(self, calendar_id: str, external_event_id: str) -> ExternalCalendarEventResult:
        token = self._access_token()
        result = self.calendar_client.get_event(access_token=token, calendar_id=calendar_id, event_id=external_event_id)
        return ExternalCalendarEventResult(result.event_id, calendar_id, "cancelled" if result.status == "cancelled" else "found")

    def find_event_by_appointment_id(self, calendar_id: str, appointment_id: int) -> ExternalCalendarEventResult | None:
        token = self._access_token()
        result = self.calendar_client.find_event_by_appointment_id(access_token=token, calendar_id=calendar_id, appointment_id=appointment_id)
        if not result:
            return None
        return ExternalCalendarEventResult(result.event_id, calendar_id, "found")

    def health_check(self) -> CalendarProviderHealth:
        try:
            self.list_calendars()
        except IntegrationError as exc:
            return CalendarProviderHealth(False, exc.code, exc.message)
        except HTTPException as exc:
            return CalendarProviderHealth(False, "google_calendar_unavailable", str(exc.detail))
        return CalendarProviderHealth(True, "ok", "Google Calendar conectado.")

    def _access_token(self) -> str:
        try:
            return self.oauth_service.access_token(self.integration_id)
        except IntegrationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
