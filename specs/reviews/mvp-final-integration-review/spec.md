# Spec - Revision integral final del MVP

## Objetivo
Validar integralmente RealMeet despues del Modulo 17, corregir solo regresiones bloqueantes y preparar la integracion del MVP completo en `staging`.

## Alcance
Incluye modulos 0-17: autenticacion, roles, catalogo, disponibilidad, reservas, UX/UI, integraciones, Google Meet, WhatsApp, n8n, calendarios externos, Google Workspace, Sheets, Docs, automatizacion documental, pagos, Mercado Pago y refunds.

## Fuera de alcance
No incluye nuevas funcionalidades, hardening profundo, CI/CD, E2E, observabilidad productiva, performance, responsive exhaustivo, accesibilidad exhaustiva, produccion real de pagos, facturacion, impuestos, boletas, conciliacion bancaria, chargebacks, workers, Redis, Celery, colas, scheduler ni merge a `main`.

## Estrategia de pruebas
- Validar Docker Compose y servicios.
- Validar Alembic current, heads, history y upgrade head.
- Ejecutar migracion desde cero en base PostgreSQL temporal aislada.
- Ejecutar suite completa backend con `pytest -q -ra`.
- Ejecutar build frontend con `npm run build`.
- Ejecutar tests/lint frontend solo si existen scripts reales.
- Validar `/health`, `/ready` y `/api/v1/openapi.json`.
- Revisar OpenAPI por JSON valido, operationIds unicos, rutas de pagos y ausencia de metadatos internos.

## Flujos criticos
- Login, rol y permisos.
- Catalogo, profesional, disponibilidad y slots.
- Reserva, confirmacion, cancelacion e historial.
- Google Meet/mock y vinculo de reunion.
- WhatsApp, email y estados de notificacion.
- Webhooks salientes, firma, entrega e idempotencia.
- Calendarios externos, FreeBusy, conflictos y eventos.
- Google Workspace: Sheets, Docs, Drive y automatizacion documental.

## Pagos
Se validan PaymentOrder, historial, Decimal, CLP sin fracciones, provider fake, politicas `no_payment`, `pay_before_confirmation`, `pay_after_confirmation`, checkout fake, Mercado Pago Checkout Pro, webhook firmado, deduplicacion, sync, retry, reconcile y refunds totales/parciales.

## Seguridad
Se revisa exposicion de secretos, tokens, datos de tarjeta, `idempotency_key`, `request_fingerprint`, payloads crudos y acceso cruzado entre roles. Se corrigen solo vulnerabilidades directas o contratos rotos.

## Criterios de aceptacion
- Suite backend completa pasa.
- Frontend compila.
- Tests/lint frontend pasan si existen.
- Alembic tiene un solo head.
- Migracion desde cero pasa.
- Health y readiness responden 200.
- OpenAPI es valido, sin operationIds duplicados y con pagos presentes.
- Schemas de pago/refund no exponen metadatos internos ni secretos.
- Flujos de pago, webhook, idempotencia, refunds y permisos estan cubiertos por tests/revision.
- Hallazgos no bloqueantes quedan documentados.
- Arbol limpio al finalizar.

## Correcciones
- Defaults compatibles en `ProfessionalPublicRead` para politica de pago publica.
- Validacion de config distingue referencias secretas legitimas de valores sensibles comunes.
- Schemas de lectura de pagos/refunds dejan de exponer `idempotency_key` y `request_fingerprint`.

## Deuda documentada
La deuda pre-MVP se mantiene en `docs/reviews/pre-mvp-integration-review.md`. Nuevos hallazgos de pagos quedan documentados en `docs/reviews/mvp-final-integration-review.md` y no bloquean staging.

## Resultado
Revision aprobada para integracion en `staging` si las validaciones post-merge se mantienen verdes.

## Decision sobre staging
Integrar mediante merge no fast-forward desde `codex/mvp-final-integration-review` hacia `staging`, validar nuevamente y publicar `staging` si no hay regresiones.
