# Submodulo 13.4 - Validacion integrada y cierre

## Objetivo

Validar de forma integrada el Modulo 13 de mensajeria WhatsApp y cerrar formalmente el alcance implementado antes de evaluar cualquier modulo posterior.

## Alcance

- Migraciones `20260715_0008` a `20260715_0011`.
- Configuracion, referencias de secretos y arranque sin credenciales reales.
- Privacidad de telefonos, HMAC, enmascaramiento y minimizacion de datos.
- Consentimiento transaccional por finalidad.
- Plantillas locales utility, sincronizacion read-only y bloqueo de marketing.
- Webhook GET/POST, firma HMAC, deduplicacion y persistencia segura.
- Cliente WhatsApp Cloud con fakes en pruebas.
- Mensajes salientes, estados, idempotencia y sincronizacion por webhook.
- Eventos de reservas, politicas de canales, fallback a email y recordatorios.
- Roles, backoffice admin, UI cliente, responsive y accesibilidad basica.
- AuditLog, logging, busquedas de secretos y datos sensibles.

## Fuera De Alcance

- Mensajes reales hacia Meta.
- Produccion o staging.
- Chat bidireccional.
- Campanas, marketing, Flows o multimedia.
- Retries automaticos generales.
- Redis, Celery, colas o locks distribuidos.
- Nuevos proveedores externos.
- Modulo 14.

## Componentes

| Componente | Estado revisado |
| --- | --- |
| `WhatsAppConsent` | Consentimiento por usuario, telefono hash y finalidad. |
| `WhatsAppTemplate` | Plantillas locales con estado, finalidad, idioma y variables permitidas. |
| `WhatsAppWebhookEvent` | Eventos reducidos con `event_key`, `payload_hash` y metadatos seguros. |
| `WhatsAppMessage` | Mensajes salientes minimizados e idempotentes. |
| `AppointmentNotification` | Trazabilidad por reserva, canal, evento, estado e intento. |
| `WhatsAppCloudClient` | Cliente HTTP aislado con fake para tests. |
| `AppointmentNotificationService` | Orquestacion transaccional de reservas, fallback y recordatorios. |
| `AdminIntegrationsPage` | Backoffice admin bajo ruta protegida existente. |
| `AppointmentsPage` | Consentimiento opcional cliente. |

## Matriz De Eventos

| Evento | Finalidad plantilla | Consentimiento |
| --- | --- | --- |
| `appointment_confirmed` | `appointment_confirmation` | `appointment_transactional` |
| `appointment_updated` | `appointment_updated` | `appointment_updates` |
| `appointment_cancelled` | `appointment_cancelled` | `appointment_updates` |
| `appointment_reminder` | `appointment_reminder` | `appointment_reminders` |
| `meeting_ready` | `meeting_ready` | `appointment_updates` |

## Matriz De Politicas

| Politica | Comportamiento |
| --- | --- |
| `email_only` | Solo email. |
| `whatsapp_preferred` | WhatsApp primero; fallback email ante fallo definitivo o consentimiento ausente. |
| `whatsapp_required` | Sin email; la reserva sigue valida aunque la notificacion falle. |
| `email_and_whatsapp` | Ambos canales con claves separadas. |
| `notifications_disabled` | No envia; registra omitido. |

## Matriz De Roles

| Rol | Permitido | Restringido |
| --- | --- | --- |
| Cliente | Gestionar su consentimiento y ver mensajes neutrales de reserva. | Backoffice, errores Meta, hashes, telefonos ajenos, retry y reconcile. |
| Profesional | Ver reservas autorizadas y estados neutrales. | Administrar WhatsApp, consentimiento detallado, retry, reconcile y errores tecnicos. |
| Admin | Configurar politica, plantillas, health, sync, webhooks, mensajes y notificaciones. | Tokens, contenido renderizado, payloads, headers, firmas y telefonos completos. |

## Riesgos Revisados

- Fuga de secretos por configuracion, logs o AuditLog.
- Exposicion de telefonos completos o hashes.
- Persistencia de payloads Meta o contenido de mensajes.
- Doble envio por idempotencia rota o scheduler repetido.
- Fallback incorrecto ante timeouts ambiguos.
- Retroceso de estados por webhooks fuera de orden.
- Regresiones en reservas, Google Meet o integraciones mock.

## Validacion Esperada

- Pruebas backend requeridas pasan.
- Suite backend completa pasa si se ejecuta.
- Build frontend pasa.
- Alembic reporta `20260715_0011 (head)`.
- `/health` y `/ready` responden correctamente.
- `git diff --check` no reporta errores.
- No hay secretos, telefonos reales, mensajes reales, push, merge, tag ni despliegue.
