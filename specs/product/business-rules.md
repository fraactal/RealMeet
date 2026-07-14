# Reglas de negocio

## Reservas

- Un profesional no puede tener dos reservas en el mismo horario.
- Un cliente no debe reservar el mismo bloque dos veces.
- Las reservas usan estados `pending`, `confirmed`, `cancelled`, `completed`, `no_show`.
- Todo cambio de estado debe registrarse en historial.
- No se deben eliminar fisicamente datos sensibles asociados a historial.

Estado observado: `AppointmentService.create` valida solapamientos del profesional para estados `pending` y `confirmed`, y crea historial inicial. No se observo restriccion de base de datos para concurrencia ni validacion explicita de que el horario solicitado pertenezca a un slot disponible.

## Disponibilidad

La disponibilidad se calcula usando reglas semanales, duracion de sesion, bloqueos manuales y reservas existentes.

Estado observado: `AvailabilityService.list_slots` genera slots desde reglas, excluye bloques y reservas. No se validaron casos borde de zona horaria, rangos largos, extra availability ni reservas canceladas.

## Privacidad

Las notas privadas del profesional nunca deben ser visibles para el cliente.

Estado observado tras `REM-P0-001`: los contratos de salida para cliente y administrador no declaran `professional_private_notes`; el contrato profesional conserva el campo solo para reservas autorizadas. Queda pendiente validacion runtime cuando el entorno lo permita.

## Seguridad

- No hardcodear secretos reales.
- Configurar JWT con expiracion.
- Configurar CORS por variables.
- No registrar passwords, tokens ni credenciales.
- Validar permisos por rol.
