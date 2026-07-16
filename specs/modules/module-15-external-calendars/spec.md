# Modulo 15 - Calendarios externos

## Objetivo

Agregar una fundacion incremental para calendarios externos en RealMeet: configuracion profesional/admin, lectura Google Calendar, FreeBusy, deteccion y aplicacion de conflictos, escritura best-effort de reservas y reconciliacion manual.

## Commits del modulo

- `c53dde8 feat(calendars): add external calendar foundation`
- `e0ea37f feat(calendars): add Google FreeBusy conflict detection`
- `16d0677 feat(calendars): enforce external conflicts on bookings`
- `f07e190 feat(calendars): sync bookings to Google Calendar`

## Arquitectura

El modulo usa contratos provider-agnostic bajo `app.calendars`, un registry de providers, `ExternalCalendarService`, `CalendarConflictService`, `ExternalAvailabilityService` y `AppointmentCalendarSyncService`.

Los providers actuales son:

- `fake`: pruebas locales sin llamadas externas.
- `google_calendar`: usa el cliente Google Calendar existente.
- `microsoft_365`: definido para futuro, no implementado.

## Modelos

- `ExternalCalendar`: calendario externo registrado por profesional.
- `CalendarSyncSettings`: politicas de lectura, conflicto, lookahead y fallo.
- `AppointmentExternalCalendarEvent`: vinculo entre una reserva y un evento externo.
- `ExternalMeeting` y `AppointmentMeeting`: se mantienen separados para Google Meet.

## OAuth

Google Calendar reutiliza el OAuth administrativo/global existente de Google Meet mediante `GoogleOAuthService` y `IntegrationCredential`. No se agrego otro flujo OAuth ni otra tabla de tokens.

## Flujo de lectura y FreeBusy

Google Calendar lista calendarios via CalendarList y consulta ocupacion via FreeBusy. La UI permite registrar un calendario Google disponible sin exponer tokens ni payloads de Google.

## Conflictos

Los conflictos usan la regla:

```text
start < busy_end AND end > busy_start
```

Bloquean `busy`, `tentative` y `out_of_office`. No bloquean `free` ni rangos adyacentes.

## Politicas

`conflict_policy`:

- `internal_only`
- `external_busy_blocks`
- `disabled`

`external_conflict_failure_policy`:

- `fail_closed`
- `fail_open`

Con `internal_only` o `disabled` no se consulta el provider externo.

## Disponibilidad y reservas

La disponibilidad interna se calcula primero. Luego, si aplica, `ExternalAvailabilityService` elimina slots con ocupacion externa.

Al crear una reserva, RealMeet revalida el rango externo justo antes de persistir. Un conflicto responde `409 external_calendar_conflict`; un fallo con `fail_closed` responde `503 external_calendar_unavailable`.

## Escritura Google Calendar

La escritura ocurre despues de persistir la reserva. Si existe calendario destino `write_enabled=true`, se crea o actualiza un evento externo best-effort. Si falla, la reserva interna no se revierte y el vinculo queda para revision manual.

## Relacion con Google Meet

Si Google Meet ya creo un evento Calendar para la reserva y pertenece al calendario destino, RealMeet reutiliza ese evento y evita duplicados. Si no existe evento Meet, se crea un evento Calendar normal sin generar enlace Meet.

## Retry y reconcile

Profesional y admin pueden consultar estado, reintentar y reconciliar manualmente. Cliente no puede administrar calendarios ni eventos externos.

## Endpoints principales

- `GET/POST/PATCH /api/v1/professionals/me/external-calendars`
- `GET/POST/PATCH /api/v1/admin/professionals/{professional_id}/external-calendars`
- `GET /api/v1/professionals/me/external-calendars/providers/google/available`
- `POST /api/v1/professionals/me/external-calendars/conflicts/check`
- `GET/PATCH /api/v1/professionals/me/calendar-sync-settings`
- `GET/POST /api/v1/professionals/me/appointments/{appointment_id}/external-calendar/*`
- `GET/POST /api/v1/admin/appointments/{appointment_id}/external-calendar/*`

## Pruebas ejecutadas

```bash
docker-compose exec -T backend pytest -q tests/test_external_calendar_foundation.py tests/test_google_calendar_conflicts.py tests/test_external_calendar_booking_enforcement.py tests/test_google_calendar_write_reconcile.py -ra
docker-compose exec -T frontend npm run build
docker-compose exec -T backend alembic current
```

## Limitaciones

- OAuth Google administrativo/global.
- Escritura en un solo calendario destino.
- Sin sincronizacion bidireccional.
- Sin Google watch, polling, workers, Redis ni retries automaticos.
- Sin transaccion distribuida con Google Calendar.
- Advertencia Vite de chunk mayor a 500 kB.

## Estado final

Modulo 15 cerrado como fundacion funcional de calendarios externos, con lectura, conflicto, enforcement de reservas, escritura best-effort, retry/reconcile manual y documentacion consolidada.
