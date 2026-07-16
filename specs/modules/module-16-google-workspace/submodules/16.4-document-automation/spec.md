# Submodulo 16.4 - Automatizacion documental

## Objetivo

Agregar automatizacion documental controlada para Google Docs operativos, reutilizando las plantillas y documentos generados del submodulo 16.3.

## Eventos

Eventos soportados:

- `appointment.created`
- `appointment.confirmed`
- `appointment.cancelled`
- `meeting.ready`

No se agregan eventos clinicos ni procesamiento asincrono.

## Reglas

`GoogleDocsAutomationRule` define integracion Google, plantilla, evento, estado habilitado, politica de comparticion, envio opcional de email y emision opcional de `document.generated` hacia webhooks/n8n.

Las reglas referencian plantillas habilitadas y evitan duplicados exactos por integracion, plantilla, evento y nombre.

## Generacion

`DocumentAutomationService` reutiliza `GoogleDocsTemplateService.generate`.

La generacion usa variables permitidas por la plantilla y no acepta variables arbitrarias. La reserva sigue siendo la fuente de verdad y los errores de automatizacion son best-effort.

## Email

El envio reutiliza SMTP/log existente mediante `EmailService`.

No se adjuntan documentos. El cuerpo incluye solo informacion minima: nombre del documento, ID de reserva y enlace Drive seguro cuando existe. No incluye notas clinicas, diagnosticos, tokens ni contenido documental.

## n8n

Cuando `n8n_event_enabled` esta activo, se publica `document.generated` usando `WebhookDeliveryService`.

El payload es minimo: documento, tipo, estado y reserva. No incluye contenido, tokens ni datos clinicos. Si no hay suscripciones, la ejecucion queda generada y n8n se marca como `skipped`.

## Idempotencia

Cada ejecucion usa:

```text
rule_id:appointment_id:event_type:event_id
```

La restriccion unica impide duplicados por reintentos de evento, timeout o accion manual repetida.

## Retry

Retry manual aplica solo a:

- `failed`
- `partially_succeeded`
- `reconcile_required`

No duplica documentos. Reintenta pasos pendientes y conserva email/n8n ya completados.

## Reconcile

Reconcile revisa existencia del documento, estado documental, email y n8n. No reenvia email ni redispacha eventos por defecto.

## Privacidad

Se mantienen variables no clinicas, sin contenido completo en base/logs, sin enlaces publicos, sin credenciales y con errores sanitizados.

## Fuera de alcance

No se implementan workers, scheduler, Celery, PDFs, adjuntos por email, Gmail API, documentos clinicos, firma electronica, webhooks Drive ni sync bidireccional.

## Criterios de aceptacion

- Existen reglas documentales y ejecuciones.
- Los eventos permitidos disparan generacion.
- La generacion reutiliza 16.3.
- Email se envia solo despues de compartir.
- `document.generated` reutiliza webhooks/n8n.
- Retry y reconcile son manuales.
- Backend protege endpoints por admin.
- Frontend administra reglas y ejecuciones.
- Pruebas especificas, Alembic y build frontend pasan.

## Pruebas

Se agrego `backend/tests/test_document_automation.py` para reglas, roles, idempotencia, email, n8n, retry, reconcile, privacidad y errores sanitizados.

## Resultado

16.4 queda como automatizacion sincrona y best-effort. No inicia 16.5.

## Limitaciones

- No hay worker ni retry automatico.
- El email no adjunta archivos.
- Reconcile es manual e individual.
- n8n depende de suscripciones webhook existentes.
