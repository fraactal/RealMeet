# Modulo 16 - Google Workspace y documentos operativos

## Objetivo

Cerrar una base operativa para Google Workspace en RealMeet sobre el OAuth Google existente, con permisos incrementales, exportacion manual a Google Sheets, generacion de documentos Google Docs almacenados en Drive y automatizacion documental controlada.

## Commits del modulo

- `30de825 feat(integrations): add Google Workspace foundation`
- `8df3900 feat(integrations): add Google Sheets appointment exports`
- `8804a70 feat(integrations): add Google Docs templates and generation`
- `40d1333 feat(integrations): add document automation workflows`

## Arquitectura

- Reutiliza `Integration`, `IntegrationCredential` e `IntegrationOAuthState`.
- Mantiene un unico OAuth Google administrativo/global.
- Usa `GoogleWorkspaceSettings` para habilitacion local, autorizacion por servicio y estado seguro.
- Centraliza servicios y scopes en `app.integrations.google_workspace.scopes`.
- Expone administracion bajo `/api/v1/admin/integrations/{id}/google/workspace`.
- El frontend integra Workspace, Sheets, Docs y automatizacion en el backoffice de integraciones.

## OAuth y permisos incrementales

El flujo incremental combina scopes ya concedidos con los solicitados por servicio y usa `include_granted_scopes=true`.

Scopes por servicio:

- Calendar y Meet: `https://www.googleapis.com/auth/calendar.events`
- Sheets: `https://www.googleapis.com/auth/spreadsheets`
- Drive: `https://www.googleapis.com/auth/drive.file`
- Docs: `https://www.googleapis.com/auth/documents`

No hay una segunda tabla de tokens. Los tokens siguen cifrados en `IntegrationCredential` y no se retornan por API.

## Modelos

- `GoogleWorkspaceSettings`
- `GoogleSheetsExportConfig`
- `GoogleSheetsExportExecution`
- `GoogleDocsTemplate`
- `AppointmentGeneratedDocument`
- `GoogleDocsAutomationRule`
- `DocumentAutomationExecution`

## Google Sheets

Google Sheets permite exportar reservas manualmente desde el backoffice.

- Configuracion por spreadsheet y pestana.
- Validacion de metadata, pestana y encabezados.
- Modos `upsert` y `append_only`.
- Idempotencia por `realmeet_appointment_id`.
- Historial de ejecuciones y retry manual.
- Limite sincronico de 366 dias y 1.000 reservas por ejecucion.

Las columnas son operativas y no incluyen notas privadas, diagnosticos, ficha clinica ni historia medica.

## Google Docs y Drive

Google Docs permite registrar plantillas operativas no clinicas.

- Plantillas origen se copian antes de modificar contenido.
- Reemplazo mediante `replaceAllText`.
- Documentos generados se vinculan a reservas con `AppointmentGeneratedDocument`.
- Drive usa `drive.file`.
- Los permisos aplicados son `reader` sobre usuarios concretos.
- No se usa acceso publico ni `anyoneWithLink`.

## Catalogo de variables

Las variables permitidas estan centralizadas en `VARIABLE_REGISTRY`.

Variables bloqueadas:

- `clinical_notes`
- `diagnosis`
- `medical_history`
- `session_notes`
- `password`
- `token`

La generacion no acepta variables arbitrarias fuera del catalogo permitido.

## Generacion manual

El admin puede generar documentos para una reserva con una plantilla habilitada y una `generation_request_id` idempotente.

Existen retry y reconcile manuales para documentos fallidos, parciales o inconsistentes.

## Automatizacion documental

`GoogleDocsAutomationRule` permite generar documentos desde eventos RealMeet de forma sincronica y best-effort.

Eventos soportados:

- `appointment.created`
- `appointment.confirmed`
- `appointment.cancelled`
- `meeting.ready`

Flujo:

```text
evento RealMeet
-> regla activa
-> ejecucion documental
-> GoogleDocsTemplateService.generate
-> sharing
-> email opcional
-> document.generated opcional
-> WebhookDeliveryService / n8n
```

La reserva sigue siendo la fuente de verdad. Fallos documentales, email o n8n no revierten la reserva.

## Email

El email opcional reutiliza el servicio SMTP/log existente. No usa Gmail API y no adjunta documentos.

El contenido es minimo: documento, reserva y enlace seguro cuando existe. No incluye notas clinicas, diagnosticos, tokens ni contenido completo.

## n8n

La automatizacion puede emitir `document.generated` mediante `WebhookDeliveryService`.

El payload es minimo:

- identificador del documento;
- tipo documental;
- estado;
- identificador de reserva.

No incluye contenido del documento, respuestas crudas de Google, tokens ni datos clinicos.

## Idempotencia, retry y reconcile

- Sheets evita duplicados por ID de reserva.
- Docs manual usa `generation_request_id`.
- Automatizacion usa `rule_id:appointment_id:event_type:event_id`.
- Retry documental no duplica documentos ni repite email/n8n ya completados.
- Reconcile es manual e individual, sin efectos secundarios externos por defecto.

## Endpoints principales

- `GET/PATCH /api/v1/admin/integrations/{id}/google/workspace`
- `POST /api/v1/admin/integrations/{id}/google/workspace/oauth/start`
- `POST /api/v1/admin/integrations/{id}/google/workspace/health`
- `POST /api/v1/admin/integrations/{id}/google/workspace/services/{service}/enable|disable|health`
- `/api/v1/admin/integrations/{id}/google/workspace/sheets/exports`
- `/api/v1/admin/integrations/{id}/google/workspace/docs/templates`
- `/api/v1/admin/appointments/{appointment_id}/documents`
- `/api/v1/admin/integrations/{id}/google/workspace/docs/automation-rules`
- `/api/v1/admin/integrations/{id}/google/workspace/docs/automation-executions`

Todos los endpoints son administrativos.

## Privacidad y seguridad

- Tokens cifrados y no retornados.
- Scopes incrementales y minimos para el flujo actual.
- Drive limitado a `drive.file`.
- Sin variables clinicas.
- Sin notas privadas, diagnosticos ni historia medica en Sheets, Docs, email o n8n.
- Permisos Drive unicamente `reader`.
- Errores Google sanitizados.
- Profesional y cliente no administran Workspace.

## Pruebas ejecutadas

Validacion de cierre prevista:

- `tests/test_google_workspace_foundation.py`
- `tests/test_google_sheets_exports.py`
- `tests/test_google_docs_templates.py`
- `tests/test_document_automation.py`
- build frontend
- Alembic current
- `/health`
- `/ready`
- `git diff --check`

## Limitaciones aceptadas

- OAuth Google administrativo/global.
- Exportaciones Sheets sincronicas.
- Limite de 366 dias y 1.000 reservas por ejecucion.
- Sin selector visual de Drive.
- Sin creacion automatica de spreadsheets.
- Generacion documental manual o sincronica.
- Email sin adjuntos.
- Retry y reconcile manuales.
- n8n depende de suscripciones existentes.
- Sin workers, scheduler, colas ni retries automaticos.
- Advertencia Vite de chunk mayor a 500 kB.

## Estado final

Modulo 16 queda cerrado con Google Workspace operativo para administracion, exportaciones Sheets manuales, documentos Docs no clinicos, almacenamiento Drive, automatizacion documental controlada, email opcional y evento `document.generated` para n8n.
