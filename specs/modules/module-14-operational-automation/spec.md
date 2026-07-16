# Modulo 14 - Automatizacion operativa

## Objetivo

Agregar una base operativa para emitir eventos de RealMeet hacia sistemas externos mediante webhooks firmados, workflows n8n y ejemplos importables, sin implementar integraciones reales de terceros desde RealMeet.

## Arquitectura

El modulo mantiene una sola infraestructura de entrega:

`evento RealMeet -> DomainEvent -> WebhookDeliveryService -> WebhookSubscription -> WebhookDelivery -> cliente HTTP/fake`

La firma, idempotencia, timeout, persistencia de entregas y retry manual estan centralizados en `WebhookDeliveryService`.

## Submodulos Implementados

- `14.1` `b7c044e feat(automation): add outbound webhook foundation`
- `14.2` `03f523e feat(automation): add n8n workflow integration`
- `14.3` `b989fca feat(automation): add operational n8n connector examples`

## Modelos Agregados

- `WebhookSubscription`
- `WebhookDelivery`
- `N8nWorkflow`

## Eventos Soportados

- `appointment.created`
- `appointment.cancelled`
- `meeting.ready`
- `notification.failed`
- `webhook.test`
- `n8n.workflow.test`

## Endpoints Principales

- `/api/v1/admin/webhook-subscriptions`
- `/api/v1/admin/webhook-deliveries`
- `/api/v1/admin/integrations/{id}/n8n/workflows`
- `/api/v1/admin/automation/examples`

## Firma E Idempotencia

Cada entrega firma el payload con HMAC-SHA256 en `X-RealMeet-Signature`, usando `X-RealMeet-Timestamp`. La idempotencia se conserva por `subscription_id` y `event_id`; una entrega exitosa no se reenvia con la misma combinacion.

## Integracion n8n

Las integraciones n8n usan `integration_type=automation` y `provider=n8n`. Cada `N8nWorkflow` referencia una `WebhookSubscription`, por lo que reutiliza la infraestructura existente y no crea un segundo sistema de deliveries.

## Payloads Operativos

`AutomationPayloadBuilder` genera payloads con `schema_version=1.0`, timestamps ISO 8601 y datos operativos sanitizados. No se exponen secretos, tokens, contrasenas, notas clinicas ni respuestas completas de proveedores. Los telefonos se enmascaran.

## Ejemplos Disponibles

- `google_sheets_appointment_log`
- `generic_crm_upsert`
- `internal_failure_notification`

Los JSON importables estan en `docs/n8n/examples/` y tambien empaquetados bajo backend para uso dentro del contenedor de desarrollo.

## Pruebas Ejecutadas En Cierre

- `tests/test_outbound_webhooks.py`
- `tests/test_n8n_workflows.py`
- `tests/test_automation_examples.py`
- build frontend
- `alembic current`
- `/health`
- `/ready`

## Limitaciones Conocidas

No se implementan Google Sheets real, CRM real, Slack real, importacion automatica a n8n, editor visual, API remota n8n, workers, colas, DLQ, retries automaticos ni observabilidad avanzada.

## Estado Final

Modulo 14 cerrado funcionalmente con validacion liviana integrada. La revision profunda de seguridad, performance, accesibilidad, responsive y produccion queda para la fase final de robustecimiento.
