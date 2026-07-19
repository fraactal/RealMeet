# Revision integral final del MVP

## Resumen ejecutivo

Estado general: aprobado para integrar a `staging`.

La revision se ejecuto sobre `codex/mvp-final-integration-review`, creada desde `e23e589 chore(payments): finalize payments module and MVP`.

Resultados pre-merge:

- Backend: `272 passed, 1 warning`.
- Frontend: build productivo correcto.
- Tests frontend: no existen scripts `test`, `npm test` ni `lint` en `frontend/package.json`.
- Migraciones: un solo head `20260719_0024`; base actual en head; migracion desde base PostgreSQL temporal vacia correcta.
- API: OpenAPI valido en `/api/v1/openapi.json`; 233 `operationId` sin duplicados; 31 rutas de pagos detectadas.
- Seguridad API pagos: schemas de pago/refund sin `idempotency_key`, `request_fingerprint`, tokens, secretos ni datos de tarjeta.
- Health: `/health` responde `200`.
- Readiness: `/ready` responde `200`.
- Docker: `backend`, `frontend` y `db` activos y healthy.

Flujos criticos validados por suite completa, pruebas especificas y revision de contratos:

- autenticacion y roles;
- catalogo, disponibilidad y reservas;
- Google Meet con fakes;
- WhatsApp y email con fakes;
- webhooks salientes y n8n;
- calendarios externos y Google Calendar con fakes;
- Google Workspace, Sheets, Docs, Drive y automatizacion documental;
- pagos fake, politicas de reserva, Mercado Pago Checkout Pro, webhook firmado, sync/retry/reconcile y refunds;
- permisos admin/profesional/cliente;
- ausencia de secretos, tarjetas y metadatos internos en contratos publicos de pagos.

Decision de integracion: la revision aprueba integrar el MVP completo, incluyendo Modulo 17, en `staging`.

## Correcciones aplicadas

### FIX-MVP-001 - Contrato publico de profesional incompatible con instancias parciales

Problema: `tests/test_auth_security.py::test_professional_public_contract_excludes_sensitive_fields` fallaba porque `ProfessionalPublicRead` exigia campos de pago introducidos por el Modulo 17 aun cuando el contrato se construia sin politica explicita.

Impacto: la suite completa fallaba y el contrato publico perdia compatibilidad con usos parciales/legacy.

Causa: los campos `price`, `payment_timing`, `payment_amount`, `payment_currency` y `payment_expiration_minutes` se agregaron sin defaults en el schema publico.

Solucion: se agregaron defaults compatibles con `no_payment` y `CLP`, y el `model_dump` publico omite campos `None` por defecto para no exponer `price` ausente como campo sensible/administrativo.

Tests:

- `docker-compose exec -T backend pytest -q tests/test_auth_security.py::test_professional_public_contract_excludes_sensitive_fields -ra`
- `docker-compose exec -T backend pytest -q -ra`

### FIX-MVP-002 - Validacion de config rechazaba referencias secretas legitimas o permitia valores sensibles segun contexto

Problema: una correccion previa para valores sensibles hacia que `access_token_reference` y `webhook_secret_reference` de Mercado Pago fueran rechazadas como valores sensibles, mientras el test legacy esperaba rechazar valores sensibles en campos comunes.

Impacto: la suite completa fallaba y Mercado Pago no podia configurarse mediante referencias de entorno.

Causa: `validate_safe_metadata` no diferenciaba entre campos comunes de config y campos terminados en `reference` que deben contener nombres de variables de entorno.

Solucion: las claves terminadas en `reference` aceptan solo referencias validas de entorno; los campos comunes siguen rechazando valores que parecen secretos.

Tests:

- `docker-compose exec -T backend pytest -q tests/test_integration_domain.py::test_integration_config_rejects_sensitive_value tests/test_mercado_pago_checkout_pro.py -ra`
- `docker-compose exec -T backend pytest -q -ra`

### FIX-MVP-003 - OpenAPI exponia metadatos internos de idempotencia en pagos

Problema: OpenAPI de pagos/refunds exponia `idempotency_key` y `request_fingerprint` en schemas administrativos.

Impacto: incumplia el criterio de seguridad minima de la revision final, aunque los campos fueran administrativos.

Causa: los modelos de lectura heredaban campos internos usados por idempotencia y auditoria operativa.

Solucion: se retiraron esos campos de los schemas de lectura de pagos/refunds y de los tipos frontend asociados. La persistencia y logica interna de idempotencia se mantiene intacta.

Tests:

- `docker-compose exec -T backend pytest -q tests/test_payment_refunds.py -ra`
- Validacion OpenAPI sin leaks en schemas de pago/refund.
- `docker-compose exec -T backend pytest -q -ra`

## Hallazgos no bloqueantes nuevos

### MVP17-PAY-001

Categoria: pagos / producto.

Severidad orientativa: media.

Descripcion: Mercado Pago esta validado con cliente fake y configuracion sandbox/controlada. No se realizaron cobros productivos reales.

Recomendacion futura: habilitar credenciales productivas, checklist operativo, monitoreo de pagos reales y prueba controlada end-to-end antes de produccion.

Bloquea staging: no.

### MVP17-PAY-002

Categoria: finanzas / operaciones.

Severidad orientativa: media.

Descripcion: refunds, retry y reconcile son manuales. No hay scheduler, workers, colas ni conciliacion bancaria automatica.

Recomendacion futura: implementar workers, conciliacion periodica, alertas de inconsistencias y trazabilidad financiera ampliada.

Bloquea staging: no.

### MVP17-PAY-003

Categoria: pagos / compliance.

Severidad orientativa: media.

Descripcion: no hay facturacion, boletas, impuestos, chargebacks completos ni conciliacion bancaria.

Recomendacion futura: definir alcance fiscal/contable y modulo financiero antes de produccion comercial.

Bloquea staging: no.

### MVP17-FE-001

Categoria: frontend / performance.

Severidad orientativa: baja.

Descripcion: Vite reporta chunk JS mayor a 500 kB (`639.77 kB`).

Recomendacion futura: code splitting y estrategia de chunks en fase de performance.

Bloquea staging: no.

### MVP17-SEC-001

Categoria: seguridad / pagos.

Severidad orientativa: media.

Descripcion: no se realizo auditoria PCI, antifraude ni hardening profundo de webhooks/rate limiting.

Recomendacion futura: ejecutar auditoria de seguridad, hardening de endpoints sensibles, rate limiting por usuario/IP y revision PCI aunque RealMeet no procese tarjetas.

Bloquea staging: no.

## Limitaciones aceptadas

- Mercado Pago sandbox/configuracion controlada.
- Sin cobros productivos.
- Sin tarjetas dentro de RealMeet.
- Refunds manuales.
- Sin facturacion.
- Sin boletas.
- Sin impuestos.
- Sin conciliacion bancaria.
- Sin chargebacks completos.
- Sin workers.
- Sin scheduler.
- Sin colas.
- Retry/reconcile manual.
- Warning Vite de chunk grande.
- Warning passlib/crypt.
- Deuda pre-MVP documentada en `docs/reviews/pre-mvp-integration-review.md` permanece no bloqueante.

## Decision

Aprobado integrar `codex/mvp-final-integration-review` en `staging` si la validacion post-merge repite suite backend, build frontend, Alembic current/heads, health, readiness y OpenAPI sin regresiones.
