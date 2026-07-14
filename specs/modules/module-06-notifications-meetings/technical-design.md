# Diseno tecnico del Modulo 6

## Backend

- `MeetingPayload` agrega `status` y `created_at` conceptuales.
- `MeetingProvider` conserva `create_meeting` y agrega operaciones conceptuales `cancel_meeting` y `get_meeting`.
- `MockMeetingProvider` genera URLs locales bajo `MOCK_MEETING_BASE_URL`.
- `AppointmentService` mantiene generacion al crear reserva para `online` y `hybrid`.
- `AppointmentService` dispara notificaciones despues de `commit` en creacion, confirmacion y cancelacion.
- `AppointmentNotificationService` compone mensajes de texto seguros y usa `EmailService`.
- `EmailService` soporta `EMAIL_MODE=log` y `EMAIL_MODE=smtp`.

## Contratos

- `AppointmentMeetingRead` expone `provider`, `join_url` y `status`.
- `AppointmentClientRead`, `AppointmentProfessionalRead` y `AppointmentAdminRead` pueden incluir `meeting`.
- Si la reserva esta cancelada, `meeting.status=inactive` y `meeting.join_url=null`.
- No se exponen `external_meeting_id`, `calendar_event_id`, credenciales ni configuracion tecnica.

## Frontend

- `AppointmentsPage` muestra modalidad, estado de reunion y enlace activo cuando corresponde.
- `ProfessionalAppointmentsPage` muestra modalidad, estado de reunion y permite copiar el enlace activo.
- `MockMeetingPage` muestra una pagina de desarrollo para `/mock-meeting/:meetingId`.

## Configuracion

- `DEFAULT_MEETING_PROVIDER=mock`
- `MOCK_MEETING_BASE_URL=http://localhost:15173/mock-meeting`
- `EMAIL_MODE=log`
- `SMTP_USE_TLS=true`
- `SMTP_TIMEOUT_SECONDS=10`

## Migraciones

No hay migracion. `Appointment` ya contiene `meeting_provider`, `meeting_url`, `external_meeting_id` y `calendar_event_id`.

## Tolerancia a fallos

El orden aplicado es:

1. ejecutar operacion de negocio;
2. hacer `commit`;
3. refrescar entidad;
4. intentar notificacion;
5. registrar resultado sin revertir la operacion.
