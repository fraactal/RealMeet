from __future__ import annotations

from datetime import datetime, timedelta

from app.calendars.contracts import BusyPeriod, CalendarProviderHealth, ExternalCalendarEventInput, ExternalCalendarEventResult, ExternalCalendarInfo


class FakeExternalCalendarProvider:
    def __init__(self, *, simulate_error: bool = False) -> None:
        self.simulate_error = simulate_error

    def _raise_if_error(self) -> None:
        if self.simulate_error:
            raise RuntimeError("fake_calendar_error")

    def list_calendars(self) -> list[ExternalCalendarInfo]:
        self._raise_if_error()
        return [
            ExternalCalendarInfo("fake-primary", "Calendario fake principal", "Calendario deterministico para pruebas.", "America/Santiago", True),
            ExternalCalendarInfo("fake-secondary", "Calendario fake secundario", "Calendario adicional para validar multiples origenes.", "America/Santiago", False),
        ]

    def list_busy_periods(self, calendar_id: str, starts_at: datetime, ends_at: datetime) -> list[BusyPeriod]:
        self._raise_if_error()
        first_start = starts_at + timedelta(hours=2)
        second_start = starts_at + timedelta(hours=5)
        return [
            BusyPeriod(first_start, min(first_start + timedelta(hours=1), ends_at), calendar_id, "fake-busy-1", "busy"),
            BusyPeriod(second_start, min(second_start + timedelta(minutes=30), ends_at), calendar_id, "fake-tentative-1", "tentative"),
        ]

    def create_event(self, payload: ExternalCalendarEventInput) -> ExternalCalendarEventResult:
        self._raise_if_error()
        return ExternalCalendarEventResult(f"fake-event-{payload.starts_at.strftime('%Y%m%d%H%M')}", payload.calendar_id, "created")

    def update_event(self, external_event_id: str, payload: ExternalCalendarEventInput) -> ExternalCalendarEventResult:
        self._raise_if_error()
        return ExternalCalendarEventResult(external_event_id, payload.calendar_id, "updated")

    def delete_event(self, calendar_id: str, external_event_id: str) -> ExternalCalendarEventResult:
        self._raise_if_error()
        return ExternalCalendarEventResult(external_event_id, calendar_id, "deleted")

    def get_event(self, calendar_id: str, external_event_id: str) -> ExternalCalendarEventResult:
        self._raise_if_error()
        return ExternalCalendarEventResult(external_event_id, calendar_id, "found")

    def find_event_by_appointment_id(self, calendar_id: str, appointment_id: int) -> ExternalCalendarEventResult | None:
        self._raise_if_error()
        return ExternalCalendarEventResult(f"fake-event-appointment-{appointment_id}", calendar_id, "found")

    def health_check(self) -> CalendarProviderHealth:
        if self.simulate_error:
            return CalendarProviderHealth(False, "fake_calendar_error", "El proveedor fake reporto un error controlado.")
        return CalendarProviderHealth(True, "ok", "Proveedor fake disponible.")
