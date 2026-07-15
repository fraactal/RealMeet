# Submodulo 14.2 - Integracion n8n y workflows operativos

## Objetivo

Agregar soporte especifico para n8n sobre la fundacion de webhooks salientes, permitiendo registrar workflows, asociarlos a eventos RealMeet y dispararlos mediante payloads firmados.

## Alcance

- Integraciones `integration_type=automation`, `provider=n8n`.
- Configuracion local no secreta: `base_url` y `environment`.
- Modelo `N8nWorkflow`.
- Workflows respaldados por `WebhookSubscription`.
- Entregas reutilizando `WebhookDelivery`.
- Test manual `n8n.workflow.test`.
- API admin y backoffice minimo.

## Fuera De Alcance

- Crear workflows mediante API n8n.
- Import/export JSON.
- Credenciales n8n.
- Ejecucion entrante desde n8n.
- Google Sheets, CRM, Slack o campanas.
- Retries automaticos, workers, colas o DLQ.

## Arquitectura Elegida

`N8nWorkflow` actua como configuracion especializada y referencia una `WebhookSubscription`. La URL final se construye desde `Integration.config.base_url` mas `webhook_path`. La firma, idempotencia, cliente y persistencia de entregas siguen en `WebhookDeliveryService`.

## Eventos

En 14.2 se reutilizan:

- `appointment.created`
- `appointment.cancelled`
- `meeting.ready`
- `notification.failed`

Ademas se agrega `n8n.workflow.test` para pruebas manuales seguras.

En esta etapa el publisher de reservas emite `appointment.created` y `appointment.cancelled`. `meeting.ready` y `notification.failed` quedan habilitados en configuracion para eventos operativos existentes o futuros sin acoplar n8n a reservas.

## API Admin

- `GET /api/v1/admin/integrations/{id}/n8n/workflows`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows`
- `GET /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}`
- `PATCH /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/enable`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/disable`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/test`
- `GET /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/deliveries`

## Seguridad

- Solo admin mediante router administrativo existente.
- `base_url` validada por `validate_target_url`.
- `webhook_path` relativo, sin esquema, traversal, query ni fragment.
- Secretos solo como `secret_reference`.
- Sin credenciales n8n, headers libres ni payloads completos.
- Firma HMAC y headers de RealMeet heredados del servicio de webhooks.
