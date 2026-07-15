# Estado De Implementacion 13.3

Estado: implementado, pendiente de validacion final integrada.

## Investigacion

- `AppointmentService` envia emails directos tras commit mediante `AppointmentNotificationService`.
- Meet se provisiona en confirmacion antes de notificar; puede quedar ready/fallback/failed.
- Email usa `EmailService` y no rompe la reserva ante fallo SMTP.
- APScheduler existe con un placeholder de recordatorios.
- WhatsApp 13.2 tiene consentimientos, plantillas, `WhatsAppMessage`, idempotencia y webhooks.

## Decision

Evolucionar `AppointmentNotificationService` a orquestador transaccional con trazabilidad en base de datos. Mantener configuracion de politica dentro de `Integration.config` de `whatsapp_cloud`.

## Avance

- Agregado modelo `AppointmentNotification` y migracion `20260715_0011`.
- Evolucionado `AppointmentNotificationService` a orquestador con politica de canal, idempotencia, builder de variables, fallback email y recordatorios.
- Integrado APScheduler existente con `appointment-reminders`.
- Sincronizados estados webhook desde `WhatsAppMessage` hacia `AppointmentNotification`.
- Agregados endpoints admin de politica y trazabilidad.
- Extendida UI admin de WhatsApp con politica, mapping y listado de notificaciones.
- Agregada captura acotada de consentimiento en la vista de reservas del cliente.
- Agregadas pruebas fake en `tests/test_appointment_whatsapp_notifications.py`.

## Limitaciones

- No se implementa preferencia individual de canal; se difiere a 13.4.
- No hay retries automaticos generales.
- Reprogramacion granular no existe en el flujo actual de reservas; el evento `appointment_updated` queda disponible para cuando exista update funcional.
- Reintento de email no tiene proveedor externo con referencia real; usa el mismo servicio SMTP/log.
