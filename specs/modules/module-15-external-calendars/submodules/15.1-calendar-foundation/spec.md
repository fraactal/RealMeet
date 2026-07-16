# Submodulo 15.1 - Fundacion de calendarios externos

## Objetivo

Crear la base provider-agnostic para que profesionales y administradores registren calendarios externos y persistan preferencias de sincronizacion futura sin modificar todavia el motor de disponibilidad ni reservas.

## Alcance

- Modelo `ExternalCalendar`.
- Modelo `CalendarSyncSettings`.
- Contratos provider-agnostic en `backend/app/calendars`.
- Provider fake deterministico.
- Registry con `fake` implementado y `google_calendar`/`microsoft_365` catalogados como no implementados.
- API profesional bajo `/api/v1/professionals/me/external-calendars`.
- API administrativa bajo `/api/v1/admin/professionals/{professional_id}/external-calendars`.
- UI profesional en Disponibilidad.
- UI administrativa acotada en Backoffice.

## Fuera De Alcance

- FreeBusy real de Google.
- Microsoft Graph.
- OAuth Microsoft.
- Sincronizacion automatica.
- Webhooks externos.
- Bloqueo real de horarios por eventos externos.
- Workers, colas, retries automaticos o DLQ.
- Modificar el motor de disponibilidad.

## Arquitectura

`ExternalCalendarService` centraliza validaciones, permisos por profesional, provider fake, health check y preferencias. Los routers solo delegan. Los providers se resuelven por `ExternalCalendarProviderRegistry`.

## Criterios De Aceptacion

- Profesional administra sus propios calendarios fake.
- Admin administra calendarios por profesional.
- Cliente recibe `403`.
- Timezones invalidas se rechazan.
- Duplicados se rechazan.
- Solo un primario por provider/profesional.
- Provider fake lista calendarios, busy periods y simula eventos.
- Providers no implementados retornan error controlado.
- No se exponen secretos.
- Migracion queda en head.
- Tests especificos y build frontend pasan.

## Pruebas Ejecutadas

- `docker-compose exec -T backend alembic upgrade head`: passed, migra a `20260716_0014`.
- `docker-compose exec -T backend pytest -q tests/test_external_calendar_foundation.py -ra`: `12 passed, 1 warning`.
- `docker-compose exec -T frontend npm run build`: passed, con advertencia Vite de chunk mayor a 500 kB.
- `docker-compose exec -T backend alembic current`: `20260716_0014 (head)`.
- `/health`: `status=ok`, `environment=docker`.
- `/ready`: `status=ready`, `database=ok`, `configuration=ok`.

## Resultado

Submodulo implementado y validado con alcance fundacional. No se conecto disponibilidad real, Google Calendar real ni Microsoft 365 real.

## Limitaciones

Google Calendar y Microsoft 365 quedan solo catalogados. `write_enabled` y `conflict_policy` se persisten para etapas futuras, pero no cambian disponibilidad real en 15.1.
