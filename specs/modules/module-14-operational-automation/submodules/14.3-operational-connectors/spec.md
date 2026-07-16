# Submodulo 14.3 - Conectores operativos y ejemplos n8n

## Objetivo

Entregar contratos de payload operativos y ejemplos importables para conectar RealMeet con workflows n8n comunes, sin implementar integraciones reales con Google Sheets, CRM o notificaciones externas desde RealMeet.

## Alcance

- Contratos `schema_version=1.0` para `appointment.created`, `appointment.cancelled`, `meeting.ready` y `notification.failed`.
- Builder centralizado `AutomationPayloadBuilder`.
- Catalogo backend de ejemplos n8n.
- Endpoints admin `GET /api/v1/admin/automation/examples` y `GET /api/v1/admin/automation/examples/{key}`.
- Workflows JSON versionados para Google Sheets, CRM generico y notificacion interna.
- Documentacion breve en `docs/n8n/README.md`.
- Seccion de backoffice "Ejemplos de automatizacion".

## Fuera De Alcance

- Credenciales reales.
- Importacion automatica hacia n8n.
- API administrativa de n8n.
- Google Sheets, CRM o Slack reales desde RealMeet.
- Workers, colas, retries automaticos, DLQ u observabilidad avanzada.
- Submodulo 14.4 y Modulo 15.

## Criterios De Aceptacion

- Payloads no exponen secretos, tokens, passwords, notas clinicas ni respuestas completas de proveedores.
- Telefonos se enmascaran.
- Catalogo referencia solo archivos existentes.
- Admin puede listar y obtener ejemplos.
- Cliente/profesional reciben `403`.
- JSONs parsean correctamente.
- Build frontend pasa.

## Pruebas Ejecutadas

- `docker-compose exec -T backend pytest -q tests/test_outbound_webhooks.py tests/test_n8n_workflows.py tests/test_automation_examples.py -ra`: `20 passed, 1 warning`.
- `docker-compose exec -T frontend npm run build`: passed, con advertencia Vite de chunk mayor a 500 kB.
- `/health`: `status=ok`, `environment=docker`.
- `/ready`: `status=ready`, `database=ok`, `configuration=ok`.

## Resultado

Submodulo implementado y validado con pruebas acotadas. No se agrego migracion porque no hubo cambios de persistencia.

## Limitaciones

Los ejemplos son guias importables y requieren revision de seguridad, autenticacion, permisos y manejo de errores antes de produccion.
