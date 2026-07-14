# Diseno tecnico del Modulo 4

## Backend

- `AvailabilityRuleCreate/Update` valida dia y rango horario.
- `AvailabilityBlockCreate/Update` valida rango de datetimes.
- `AvailabilityResponse` encapsula profesional, rango y slots.
- `AvailabilityService` concentra propiedad, solapamientos, rangos y calculo de slots.
- Los routers solo resuelven usuario, parametros y respuesta HTTP.

## Persistencia

No hay cambios de esquema. Se reutilizan `availability_rules` y `availability_blocks` de la migracion inicial.

## Propiedad

Los endpoints `me/*` cargan el perfil profesional desde el usuario autenticado y luego buscan reglas/bloqueos por `professional_id`. Si el recurso no pertenece al profesional, responde `404`.

## Slots

El calculo usa datetimes UTC. Las fechas publicas (`date`, `date_from`, `date_to`) se interpretan como dias UTC. Esta decision es suficiente para el MVP local; soporte avanzado de zonas horarias queda diferido.

## Frontend

- `ProfessionalAvailabilityPage` administra reglas y bloqueos.
- `ProfessionalsPage` agrega selector de fecha y slots deshabilitados en detalle.
- La UI no crea reservas.

## Validacion

Pruebas minimas cubren:

- rango horario invalido;
- rango de bloqueo invalido;
- regla solapada;
- exclusion de slot bloqueado.
