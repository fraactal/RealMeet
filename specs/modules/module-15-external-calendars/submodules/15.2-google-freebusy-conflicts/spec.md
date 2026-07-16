# Submodulo 15.2 - Google FreeBusy y deteccion de conflictos

## Objetivo

Permitir lectura real de ocupacion desde Google Calendar mediante CalendarList y FreeBusy, y previsualizar conflictos sin modificar todavia el flujo real de reservas ni el motor publico de disponibilidad.

## Alcance

- Provider `GoogleExternalCalendarProvider`.
- Extension acotada de `GoogleCalendarClient` con `calendarList` y `freeBusy`.
- Reutilizacion de `GoogleOAuthService`, tokens cifrados e integracion Google existente.
- Listado de calendarios Google disponibles para profesional y admin.
- Registro validado de calendarios `google_calendar`.
- `CalendarConflictService` con reglas de solapamiento.
- Endpoints de previsualizacion de conflictos.
- UI profesional/admin para buscar Google y probar rangos.

## Fuera De Alcance

- Bloqueo efectivo de reservas.
- Cambios al endpoint publico de disponibilidad.
- Escritura, actualizacion o eliminacion real de eventos Google.
- Sync periodica, polling, push notifications, workers, colas, DLQ o retries automaticos.
- Microsoft 365 real.

## Reutilizacion De OAuth

Se reutiliza el OAuth administrativo Google existente, `IntegrationCredential` y `TokenCipher`. No se crean tablas nuevas de tokens ni un segundo flujo OAuth. Limitacion: el OAuth actual es global/administrativo y no esta asociado de forma nativa a cada profesional; por eso 15.2 usa la integracion Google conectada existente mediante `integration_id` o la integracion Google disponible por defecto.

## Arquitectura

`ExternalCalendarService` valida calendarios disponibles y providers. `GoogleExternalCalendarProvider` adapta Google Calendar al contrato comun. `CalendarConflictService` consulta calendarios habilitados con `read_enabled` y `conflict_check_enabled`, respeta `CalendarSyncSettings` y devuelve conflictos o errores resumidos.

## Privacidad

FreeBusy solo retorna intervalos ocupados. RealMeet no solicita ni expone titulos, asistentes, ubicacion, notas, descripciones, tokens ni respuestas crudas de Google.

## Criterios De Aceptacion

- Google lista calendarios con cliente fake en tests.
- FreeBusy se transforma a `BusyPeriod`.
- Se validan calendarios antes de registrarlos.
- Rangos adyacentes no generan conflicto.
- `internal_only` y `disabled` omiten consulta externa.
- `external_busy_blocks` consulta provider.
- Errores parciales se resumen.
- Cliente recibe `403`.
- Admin puede consultar por profesional.
- Frontend compila.

## Pruebas

- `docker-compose exec -T backend pytest -q tests/test_external_calendar_foundation.py tests/test_google_calendar_conflicts.py -ra`: `20 passed, 1 warning`.
- `docker-compose exec -T frontend npm run build`: passed, con advertencia Vite de chunk mayor a 500 kB.
- `docker-compose exec -T backend alembic current`: `20260716_0014 (head)`.
- `/health`: `status=ok`, `environment=docker`.
- `/ready`: `status=ready`, `database=ok`, `configuration=ok`.

## Resultado

Submodulo implementado y validado. No se agrego migracion porque los modelos de 15.1 ya soportaban la asociacion necesaria.

## Limitaciones

No hay enforcement en reservas, no hay sync automatica y no se implementa Microsoft 365.
