# Submodulo 15.3 - Aplicacion de conflictos externos a disponibilidad y reservas

## Objetivo

Aplicar los periodos ocupados de calendarios externos al flujo real de disponibilidad y creacion de reservas, reutilizando la fundacion de calendarios externos y Google FreeBusy de 15.1 y 15.2.

## Reglas de disponibilidad

RealMeet mantiene primero el calculo interno existente: reglas semanales, bloqueos manuales, reservas activas y duracion de sesion.

Cuando el profesional tiene `sync_enabled=true`, `conflict_policy=external_busy_blocks` y calendarios externos habilitados para lectura y chequeo de conflictos, el backend consulta solo la ventana pedida y elimina slots que se solapan con periodos externos `busy`, `tentative` u `out_of_office`.

Los periodos `free` no bloquean. Los rangos adyacentes no bloquean.

La respuesta publica de disponibilidad sigue mostrando solo slots disponibles. No expone calendario, evento, provider, integracion ni errores crudos.

## Validacion final de reservas

Antes de crear una reserva, el servicio mantiene las validaciones internas y el control de solapamiento existente. Luego vuelve a consultar disponibilidad externa justo antes de persistir la cita.

Si hay conflicto externo, la cita no se crea y se responde `409 Conflict` con codigo `external_calendar_conflict` y mensaje seguro.

Si el proveedor externo no esta disponible y la politica exige bloqueo, la cita no se crea y se responde `503 Service Unavailable` con codigo `external_calendar_unavailable`.

## Politicas de fallo

Se agrego `external_conflict_failure_policy` en `CalendarSyncSettings`.

Valores:

- `fail_closed`: default seguro. Si no se puede comprobar el proveedor externo, se ocultan nuevos slots cuando es viable y se bloquea la reserva.
- `fail_open`: si el proveedor falla, se continua con disponibilidad interna y con los calendarios externos que si respondieron.

## Privacidad

Los errores externos se resumen sin tokens, payloads, titulos de eventos, asistentes, descripciones ni identificadores privados de eventos.

El frontend muestra mensajes orientados al usuario y no detalles tecnicos del proveedor.

## Fuera de alcance

No se implemento escritura en Google Calendar, sincronizacion bidireccional, almacenamiento local de FreeBusy, polling, scheduler, workers, Redis, Microsoft 365 ni refactor general del motor de reservas.

## Criterios de aceptacion

- La disponibilidad puede excluir slots por ocupacion externa.
- La reserva se revalida contra calendarios externos antes de persistirse.
- `fail_closed` y `fail_open` funcionan por profesional.
- El default es `fail_closed`.
- Los errores son controlados y sanitizados.
- No se crean eventos externos.
- El frontend permite configurar la politica de fallo.
- Las pruebas acotadas pasan y el frontend compila.

## Pruebas

Comando ejecutado:

```bash
docker-compose exec -T backend pytest -q tests/test_external_calendar_foundation.py tests/test_google_calendar_conflicts.py tests/test_external_calendar_booking_enforcement.py -ra
```

Resultado:

```text
31 passed, 1 warning
```

Build frontend:

```bash
docker-compose exec -T frontend npm run build
```

Resultado: exitoso, con advertencia existente de chunk mayor a 500 kB.

## Resultado

15.3 queda implementado con migracion `20260716_0015`, servicio central `ExternalAvailabilityService`, integracion en disponibilidad publica y validacion final de reservas.

## Limitaciones

No existe transaccion distribuida con Google Calendar. Puede ocurrir un cambio externo inmediatamente despues de la comprobacion y antes de que el cliente reciba la confirmacion.

La ruta activa integrada es el endpoint principal de disponibilidad usado por el flujo de reserva. Si aparecen rutas alternativas futuras, deben conectarse al mismo servicio central.
