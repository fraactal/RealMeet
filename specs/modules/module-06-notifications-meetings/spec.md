# Modulo 6 - Notificaciones, correo y MockMeetingProvider

## Problema

El flujo de reservas ya permite crear y gestionar estados, pero la comunicacion asociada y la reunion simulada estaban incompletas: el mock existia de forma basica, las notificaciones no cubrian confirmacion/cancelacion y el correo no era tolerante a fallos.

## Objetivo

Integrar notificaciones basicas y datos de reunion simulada al ciclo de reservas sin implementar proveedores reales ni colas externas.

## Alcance

- Robustecer `MeetingProvider` y `MockMeetingProvider`.
- Mantener Google Meet y Zoom como placeholders no funcionales.
- Generar reunion mock para reservas remotas `online` o `hybrid`.
- No generar reunion para reservas `presencial`.
- Exponer datos de reunion mediante contrato seguro.
- Registrar reunion cancelada como inactiva por estado calculado.
- Enviar o registrar notificaciones de creacion, confirmacion y cancelacion.
- Operar en modo `log` sin SMTP.
- Operar con SMTP si la configuracion externa existe.
- Evitar que fallos de correo rompan reservas.
- Mostrar datos de reunion en frontend cliente y profesional.
- Agregar pagina simple de mock meeting.

## Exclusiones

- Google Meet real.
- Zoom real.
- Google Calendar.
- WhatsApp, SMS y push.
- Pagos.
- Celery, RabbitMQ, Redis obligatorio o colas externas.
- Reintentos distribuidos.
- Plantillas HTML avanzadas.
- Adjuntos e invitaciones `.ics`.
- WebRTC, audio, video o chat real.

## Actores

- Cliente asociado: ve datos de reunion de sus reservas y recibe notificaciones basicas.
- Profesional asociado: ve datos de reunion de sus reservas y recibe notificaciones basicas.
- Administrador: mantiene vista minima de reservas sin notas privadas ni credenciales.

## Eventos notificables

- Reserva creada: cliente y profesional.
- Reserva confirmada: cliente y profesional, con enlace de reunion si aplica.
- Reserva cancelada: cliente y profesional, sin notas privadas.

`completed` y `no_show` no generan correo en este modulo.

## Politica de reuniones

La politica actual se mantiene: la reunion se crea al crear la reserva para modalidades `online` y `hybrid`. La decision conserva coherencia con el Modulo 5, que ya persistia datos de reunion al crear.

La modalidad se almacena en `Appointment.consultation_mode`, copiada desde el perfil profesional al crear la reserva.

Una reserva `presencial` no obtiene reunion. Una reserva cancelada conserva los datos historicos en base de datos, pero el contrato marca la reunion como `inactive` y no entrega `join_url`.

## Estrategia SMTP y modo desarrollo

`EMAIL_MODE=log` es el modo predeterminado. En ese modo se registra la notificacion sin contactar servidores externos.

`EMAIL_MODE=smtp` usa `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`, `SMTP_USE_TLS` y `SMTP_TIMEOUT_SECONDS`.

Las credenciales SMTP no se registran.

## Seguridad y riesgos

Riesgos identificados:

- Enlace de reunion expuesto a usuarios no asociados.
- Link de reserva cancelada presentado como activo.
- Notas privadas incluidas en notificaciones.
- Secretos SMTP registrados en logs.
- Fallos de correo revirtiendo una reserva valida.

Controles implementados:

- Datos de reunion via contratos de reserva protegidos por `get_for_actor`.
- `join_url` se omite cuando la reserva esta cancelada.
- Plantillas de texto no incluyen notas privadas.
- Logs de correo no imprimen password ni usuario SMTP.
- `EmailService` y `AppointmentNotificationService` capturan fallos y retornan resultado controlado.

Riesgos residuales:

- No hay enlaces expirables.
- No hay delivery tracking.
- No hay cola ni reintentos.
- No se valida SMTP real en este modulo.
- La pagina mock es publica por simplicidad de desarrollo; el enlace solo se obtiene desde reservas autorizadas.

## Validaciones finales

- Backend tests.
- Frontend build.
- `/health` y `/ready`.
- Runtime: reserva remota, confirmacion, reunion mock visible para cliente/profesional, acceso ajeno rechazado, log de notificacion, cancelacion con reunion inactiva.
