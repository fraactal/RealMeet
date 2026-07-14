# Diseno tecnico del Modulo 5

## Backend

- `AppointmentCreate` recibe `professional_id`, `specialty_id`, `start_datetime` y nota cliente.
- `AppointmentHistoryRead` se agrega a contratos de salida.
- `AppointmentClientRead` y `AppointmentAdminRead` no incluyen notas privadas.
- `AppointmentProfessionalRead` incluye notas privadas solo para profesional autorizado.
- `AppointmentService` concentra validacion de disponibilidad, conflictos, transiciones, historial y notas.

## Doble reserva

Se agregan indices unicos parciales:

- profesional + inicio + termino cuando `status in ('pending', 'confirmed')`;
- cliente + inicio + termino cuando `status in ('pending', 'confirmed')`.

El servicio tambien valida conflictos antes de insertar y traduce `IntegrityError` a `409`.

## Disponibilidad

La creacion usa `AvailabilityService.list_slots` para validar que el intervalo exacto exista. Esto reusa reglas, bloqueos y reservas activas del Modulo 4.

## Estados

Mapa de transiciones:

- Cliente: `pending/confirmed -> cancelled` si futura.
- Profesional: `pending -> confirmed`, `pending/confirmed -> cancelled`, `confirmed -> completed`, `confirmed -> no_show`.

## Frontend

- El detalle publico de profesional permite crear una reserva desde un slot.
- `AppointmentsPage` permite listar y cancelar para cliente.
- `ProfessionalAppointmentsPage` permite confirmar, cancelar, completar, marcar no show y editar nota privada.

## Migracion

Nueva migracion Alembic agrega indices unicos parciales con precheck de duplicados activos.
