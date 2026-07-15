# Submodulo 13.3 - Reservas, recordatorios y fallback a email

## Objetivo

Conectar WhatsApp Cloud con eventos transaccionales de reservas sin bloquear el ciclo de vida de una reserva si falla un canal externo.

## Alcance

- Eventos internos: `appointment_confirmed`, `appointment_updated`, `appointment_cancelled`, `appointment_reminder`, `meeting_ready`.
- Politica centralizada en `Integration.config` para `whatsapp_cloud`.
- Trazabilidad en `AppointmentNotification`.
- Envio WhatsApp al cliente con consentimiento activo, plantilla utility aprobada e idempotencia.
- Fallback a email mediante el servicio SMTP/log existente.
- Recordatorios con APScheduler existente y una ventana configurable.
- API admin para listar, reintentar, reconciliar y cancelar notificaciones.
- Backoffice en la pantalla de integraciones.

## Fuera De Alcance

- Mensajes libres, chatbot, respuestas entrantes, campanas, multimedia, Flows.
- Redis, Celery, colas externas o retries automaticos generales.
- Proveedores externos adicionales, n8n, Twilio o marketing.
- Preferencia de canal por usuario; queda como deuda.

## Eventos De Reserva

Los eventos solo transportan referencias seguras: appointment ID, user ID, professional ID, tipo de evento, fecha y version. Las variables se reconstruyen desde la reserva en cada intento.

## Politica De Canales

Valores soportados:

- `email_only`
- `whatsapp_preferred`
- `whatsapp_required`
- `email_and_whatsapp`
- `notifications_disabled`

La ausencia o revocacion de consentimiento se trata como `skipped` de WhatsApp, no como fallo tecnico. En `whatsapp_preferred` habilita fallback a email. En timeouts ambiguos no se aplica fallback inmediato.

## Configuracion

La politica vive en `Integration.config.notification_policy` junto a:

- `fallback_channel`
- `reminder_enabled`
- `reminder_minutes_before`
- `template_mapping`
- `default_language`

No se guardan secretos ni canales arbitrarios.

## Consentimiento

Se valida por finalidad al momento del envio:

- confirmacion: `appointment_transactional`
- actualizacion/cancelacion/meeting ready: `appointment_updates`
- recordatorio: `appointment_reminders`

## Plantillas Y Variables

Solo se eligen plantillas `utility`, `approved`, con finalidad e idioma compatibles. Variables permitidas: nombre breve de cliente, profesional, fecha, hora, modalidad, `meeting_url` si existe y plataforma.

## Idempotencia

La clave combina reserva, evento, version y canal. Cada canal tiene clave separada y unique constraint. El scheduler repetido no duplica recordatorios.

## Transacciones

La reserva se persiste antes de notificar. Las llamadas externas ocurren despues y no revierten la reserva. El resultado queda en `AppointmentNotification`.

## Scheduler

Se reutiliza APScheduler. Selecciona reservas confirmadas futuras dentro de la ventana configurada y reclama notificaciones por idempotencia.

## Backoffice

Admin puede revisar notificaciones, reintentar fallidas, reconciliar desde `WhatsAppMessage` y cancelar pendientes. No se muestran contenido, variables, telefono completo, payloads ni tokens.

## Deuda Para 13.4

- Preferencia individual de canal.
- Reconciliacion read-only contra Meta si se define endpoint seguro.
- Reintento manual de email con referencia externa real.
- Multiples recordatorios configurables.
