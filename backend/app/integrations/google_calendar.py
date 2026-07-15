from dataclasses import dataclass
from datetime import datetime
import time
from typing import Protocol
from urllib.parse import quote

import httpx

from app.integrations.exceptions import IntegrationProviderExecutionError
from app.integrations.meeting_contracts import MeetingCreateRequest


@dataclass
class CalendarEventResult:
    event_id: str
    html_link: str | None
    hangout_link: str | None
    conference_id: str | None
    conference_status: str
    status: str
    start_at: datetime
    end_at: datetime


class GoogleCalendarClient(Protocol):
    def create_event(self, *, access_token: str, calendar_id: str, request: MeetingCreateRequest, request_id: str) -> CalendarEventResult:
        ...

    def get_event(self, *, access_token: str, calendar_id: str, event_id: str) -> CalendarEventResult:
        ...

    def delete_event(self, *, access_token: str, calendar_id: str, event_id: str, send_updates: str) -> None:
        ...

    def get_calendar(self, *, access_token: str, calendar_id: str) -> dict:
        ...


class GoogleCalendarHTTPClient:
    base_url = "https://www.googleapis.com/calendar/v3"

    def create_event(self, *, access_token: str, calendar_id: str, request: MeetingCreateRequest, request_id: str) -> CalendarEventResult:
        response = httpx.post(
            f"{self.base_url}/calendars/{quote(calendar_id, safe='')}/events",
            params={"conferenceDataVersion": "1", "sendUpdates": request.send_updates},
            headers=_headers(access_token),
            json=_event_body(request, request_id),
            timeout=10,
        )
        data = _json_or_raise(response)
        return _parse_event(data, request.start_at, request.end_at)

    def get_event(self, *, access_token: str, calendar_id: str, event_id: str) -> CalendarEventResult:
        response = httpx.get(
            f"{self.base_url}/calendars/{quote(calendar_id, safe='')}/events/{quote(event_id, safe='')}",
            headers=_headers(access_token),
            timeout=10,
        )
        data = _json_or_raise(response)
        return _parse_event(data, _parse_datetime(data["start"]["dateTime"]), _parse_datetime(data["end"]["dateTime"]))

    def delete_event(self, *, access_token: str, calendar_id: str, event_id: str, send_updates: str) -> None:
        response = httpx.delete(
            f"{self.base_url}/calendars/{quote(calendar_id, safe='')}/events/{quote(event_id, safe='')}",
            params={"sendUpdates": send_updates},
            headers=_headers(access_token),
            timeout=10,
        )
        if response.status_code in {200, 204, 410}:
            return
        if response.status_code == 404:
            return
        _json_or_raise(response)

    def get_calendar(self, *, access_token: str, calendar_id: str) -> dict:
        response = httpx.get(f"{self.base_url}/calendars/{quote(calendar_id, safe='')}", headers=_headers(access_token), timeout=10)
        return _json_or_raise(response)


def wait_for_conference(client: GoogleCalendarClient, *, access_token: str, calendar_id: str, event: CalendarEventResult) -> CalendarEventResult:
    if event.conference_status != "pending" or event.hangout_link:
        return event
    current = event
    for _ in range(2):
        time.sleep(0.2)
        current = client.get_event(access_token=access_token, calendar_id=calendar_id, event_id=event.event_id)
        if current.conference_status != "pending" or current.hangout_link:
            return current
    return current


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json", "Content-Type": "application/json"}


def _event_body(request: MeetingCreateRequest, request_id: str) -> dict:
    body = {
        "summary": request.title,
        "description": request.description,
        "start": {"dateTime": request.start_at.isoformat(), "timeZone": request.timezone},
        "end": {"dateTime": request.end_at.isoformat(), "timeZone": request.timezone},
        "conferenceData": {
            "createRequest": {
                "requestId": request_id,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
    if request.attendees:
        body["attendees"] = [{"email": attendee.email} for attendee in request.attendees]
    return body


def _json_or_raise(response: httpx.Response) -> dict:
    if response.status_code >= 400:
        code = "google_calendar_error"
        if response.status_code == 404:
            code = "google_calendar_not_found"
        if response.status_code == 403:
            code = "google_calendar_permission_denied"
        if response.status_code == 429:
            code = "google_calendar_rate_limited"
        raise IntegrationProviderExecutionError("Google Calendar rechazo la operacion", code=code)
    return response.json()


def _parse_event(data: dict, fallback_start: datetime, fallback_end: datetime) -> CalendarEventResult:
    conference = data.get("conferenceData") or {}
    status = ((conference.get("createRequest") or {}).get("status") or {}).get("statusCode") or "success"
    meeting_url = data.get("hangoutLink") or _video_entrypoint(conference)
    return CalendarEventResult(
        event_id=data["id"],
        html_link=data.get("htmlLink"),
        hangout_link=meeting_url,
        conference_id=conference.get("conferenceId"),
        conference_status=status,
        status=data.get("status", "confirmed"),
        start_at=_parse_datetime((data.get("start") or {}).get("dateTime")) if (data.get("start") or {}).get("dateTime") else fallback_start,
        end_at=_parse_datetime((data.get("end") or {}).get("dateTime")) if (data.get("end") or {}).get("dateTime") else fallback_end,
    )


def _video_entrypoint(conference: dict) -> str | None:
    for item in conference.get("entryPoints") or []:
        if item.get("entryPointType") == "video":
            return item.get("uri")
    return None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
