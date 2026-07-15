# Submodulo 14.1 - Webhooks salientes y contratos de eventos

## Objetivo

Crear la base para emitir eventos operativos firmados desde RealMeet hacia sistemas externos, sin implementar todavia n8n ni workflows concretos.

## Alcance

- Catalogo de eventos operativos.
- Contrato interno versionado `v1`.
- Suscripciones webhook vinculadas a integraciones `generic_webhook` o `n8n`.
- Entregas persistidas con idempotencia por suscripcion y evento.
- Firma HMAC-SHA256 con secreto resuelto desde variable de entorno.
- Cliente HTTP real y fake para pruebas.
- API admin minima.
- Backoffice minimo dentro de Integraciones.
- Conexion inicial de `appointment.created` y `appointment.cancelled`.

## Fuera De Alcance

- n8n real.
- Workflows visuales o reglas de negocio externas.
- Retries automaticos, colas, workers o DLQ.
- Webhooks entrantes genericos.
- Payloads completos, secretos, notas privadas, datos clinicos, telefonos, emails o meeting URLs.

## Contrato De Evento

Cada evento contiene:

- `event_id`
- `event_type`
- `event_version`
- `occurred_at`
- `entity_type`
- `entity_id`
- `correlation_id`
- `payload`

El payload de reservas usa solo IDs y datos operativos minimos.

## Eventos Catalogados

- `appointment.created`
- `appointment.updated`
- `appointment.cancelled`
- `appointment.confirmed`
- `meeting.ready`
- `notification.sent`
- `notification.failed`
- `client.created`
- `professional.created`
- `webhook.test`

En 14.1 solo se conectan `appointment.created` y `appointment.cancelled`, mas `webhook.test` para pruebas manuales.

## Seguridad

- URLs HTTPS, salvo localhost en entorno local/test/docker/development.
- Sin credenciales embebidas en URL.
- IPs privadas y localhost bloqueados fuera de entorno local.
- No se siguen redirects.
- Secreto por referencia de entorno, nunca persistido.
- Firma en `X-RealMeet-Signature`.
- Headers: `X-RealMeet-Event`, `X-RealMeet-Delivery`, `X-RealMeet-Timestamp`.
- No se persiste response body.

## Validacion

- Pruebas backend acotadas de 14.1.
- Build frontend.
- Alembic upgrade/current.
- `/health` y `/ready`.
