# Submodulo 15.4 - Escritura en Google Calendar y reconciliacion manual

## Objetivo

Permitir que una reserva de RealMeet mantenga un vinculo persistente con un evento de calendario externo cuando el profesional tenga un calendario write-enabled. La reserva interna sigue siendo la fuente de verdad.

## Relacion con Google Meet

Google Meet ya crea eventos en Google Calendar cuando la politica de reuniones lo requiere. Si la reserva ya tiene un evento Google Meet listo y pertenece al mismo calendario destino, RealMeet reutiliza ese `external_event_id` y no crea un segundo evento.

Si no existe evento Meet, se crea un evento de calendario normal sin generar enlace Meet.

## Creacion

El destino de escritura se resuelve por:

1. `CalendarSyncSettings.default_external_calendar_id` si esta habilitado para escritura;
2. calendario `is_primary=true` con `write_enabled=true`;
3. sin destino, no se escribe externamente.

El evento contiene titulo, descripcion minima, inicio, termino, timezone, asistentes seguros y `extendedProperties.private.realmeet_appointment_id`.

## Actualizacion

Ante cambios internos relevantes expuestos por el flujo actual, el servicio puede actualizar el evento vinculado. Si falla, la reserva interna no se revierte y el vinculo queda `reconcile_required`.

## Cancelacion

Cuando una reserva se cancela, se intenta eliminar/cancelar el evento externo best-effort. Si falla, la cancelacion interna se conserva y el vinculo queda pendiente de reconciliacion.

## Idempotencia

La tabla `appointment_external_calendar_events` tiene una restriccion unica por `appointment_id` y `external_calendar_id`. Retry y reprocesos reutilizan el vinculo existente para evitar duplicados.

## Retry

Retry reejecuta la accion pendiente: create, update o cancel. No hay retries automaticos ni workers.

## Reconcile

Reconcile consulta el evento por `external_event_id` o intenta encontrarlo mediante `realmeet_appointment_id`. Puede marcar el vinculo como sincronizado, cancelado o `reconcile_required`.

## Seguridad

No se almacenan tokens, payloads completos de Google, notas clinicas, motivos sensibles ni respuestas crudas. Los errores persistidos son resumidos.

## Fuera de alcance

No se implementa sincronizacion bidireccional, polling, Google watch, workers, Redis, Microsoft 365, reconciliacion masiva ni escritura en multiples calendarios.

## Pruebas

Comando ejecutado:

```bash
docker-compose exec -T backend pytest -q tests/test_external_calendar_foundation.py tests/test_google_calendar_conflicts.py tests/test_external_calendar_booking_enforcement.py tests/test_google_calendar_write_reconcile.py -ra
```

Resultado:

```text
39 passed, 1 warning
```

Build frontend:

```bash
docker-compose exec -T frontend npm run build
```

Resultado: exitoso, con advertencia existente de chunk mayor a 500 kB.

## Resultado

15.4 agrega el modelo `AppointmentExternalCalendarEvent`, la migracion `20260716_0016`, escritura Google Calendar desde el provider existente, sync best-effort en reservas, endpoints manuales profesional/admin y paneles acotados en frontend.

## Limitaciones

No existe transaccion distribuida con Google Calendar. Un cambio externo puede ocurrir despues de reconciliar. La actualizacion automatica se limita a los cambios que hoy pasan por el servicio de reservas existente.
