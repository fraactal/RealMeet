# Estado De Implementacion 14.2

Estado: implementado y validado.

## Decisiones

- No se crea un segundo delivery service.
- `N8nWorkflow` mantiene datos administrativos y referencia a `WebhookSubscription`.
- La suscripcion guarda la URL final derivada para aprovechar idempotencia y entregas existentes.
- n8n no se llama por API; solo recibe webhooks firmados.

## Implementado

- Migracion `20260715_0013_n8n_workflows`.
- Modelo `N8nWorkflow`.
- Validacion de configuracion n8n.
- Servicio `N8nWorkflowService`.
- API admin para CRUD parcial, enable/disable, test y entregas.
- Backoffice dentro de Integraciones admin.
- Tipos y API frontend.
- Pruebas acotadas `tests/test_n8n_workflows.py`.

## Limitaciones

- No hay editor visual ni import/export de workflows n8n.
- No se administran credenciales n8n.
- No hay inbound desde n8n.
- No hay colas, retries automaticos ni DLQ.
