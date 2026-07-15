# Submodulo 11.2 - Servicios, proveedor mock y API administrativa

## Objetivo

Implementar la capa de aplicacion para administrar integraciones desde backend: contrato comun de proveedores, registry, proveedor mock seguro, servicio transaccional, auditoria y API administrativa protegida.

## Alcance

- Contrato comun de proveedor.
- Resultados internos normalizados.
- Excepciones de dominio sin dependencia de FastAPI.
- Registry central con soporte solo para `mock`.
- Proveedor mock/no-op sin red.
- Servicio de integraciones.
- Validacion, habilitacion, deshabilitacion, health check y test mock.
- Idempotencia runtime sobre `IntegrationExecution`.
- AuditLog seguro.
- Endpoints admin bajo `/api/v1/admin/integrations`.
- Pruebas backend acotadas.

## Fuera de alcance

- Frontend, navegacion y backoffice.
- Google Meet real, WhatsApp, Twilio, n8n, calendarios o webhooks.
- Cambios a reservas, reuniones mock existentes, SMTP o APScheduler.
- Workers, colas, reintentos automaticos o llamadas externas.

## Contratos internos

`IntegrationProvider` define tres operaciones genericas:

- `validate_configuration(integration)`.
- `health_check(integration)`.
- `execute(integration, operation, payload)`.

Los providers no acceden a FastAPI, routers ni sesion de base de datos.

## Operaciones soportadas

En 11.2 solo el proveedor `mock` soporta:

- validacion de configuracion;
- health check;
- ejecucion `test`.

Los proveedores futuros son conocidos por enum, pero no soportados por registry.

## Proveedor mock

Configuracion permitida:

- `simulate_error: bool = false`
- `health: "healthy" | "error" = "healthy"`
- `response_delay_ms: int = 0..250`

No ejecuta red, no escribe archivos, no modifica reservas y no envia mensajes.

## Autorizacion

Todos los endpoints usan el guard admin existente. Usuarios sin token reciben 401; cliente o profesional reciben 403.

## Idempotencia

El servicio busca `IntegrationExecution` por `(integration_id, idempotency_key)`.

- `succeeded`: devuelve resultado omitido/idempotente sin invocar provider.
- `pending` o `running`: falla con conflicto.
- `failed`: reutiliza la fila, incrementa `attempt` y reintenta manualmente.

## Auditoria

Se registra `AuditLog` para crear, actualizar, habilitar, deshabilitar, validar, health check y test. La metadata contiene solo ID, proveedor, tipo, resultado y campos modificados; no contiene config completa, metadata completa ni `secret_reference`.

## Errores

El servicio lanza excepciones de dominio. El router las traduce a HTTP:

- no encontrado: 404;
- configuracion invalida: 422;
- proveedor no soportado: 409;
- integracion deshabilitada: 409;
- ejecucion en proceso: 409;
- error inesperado: 500 generico.

## Seguridad

- Schemas explicitos con `extra="forbid"`.
- Sin mass assignment.
- Sin secretos en config, metadata, logs, auditoria o respuestas.
- Mock sin red.
- Proveedores futuros no habilitables.
- Listados limitados.

## Pruebas

Pruebas acotadas cubren registry/provider, servicio, idempotencia, auditoria, API admin y autorizacion.

## Relacion con 11.3

11.3 consumira esta API para crear el backoffice de integraciones y agregar navegacion administrativa. No se implementa frontend en 11.2.
