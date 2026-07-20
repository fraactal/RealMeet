# RealMeet - Roadmap de preparacion productiva

Este roadmap parte desde `staging` en commit base `651f3a4` y no implementa correcciones.

## Orden recomendado

1. Staging desplegable.
2. CI minima.
3. Secretos y configuracion.
4. Backups y observabilidad.
5. Pruebas E2E criticas.
6. Integraciones sandbox reales.
7. Seguridad profunda.
8. Performance.
9. Responsive y accesibilidad.
10. Produccion.

## Plan de ramas

- `main`: rama estable promovida solo despues de aprobacion.
- `staging`: rama de integracion y despliegue previo.
- `codex/hardening-*`: ramas acotadas por fase o subfase.

Flujo:

```text
staging
-> rama de hardening acotada
-> validacion especifica
-> PR a staging
-> validacion staging
-> promocion posterior a main
```

## Estrategia de commits

Mantener un commit por fase o subfase completa cuando sea razonable. Evitar commits por archivo, commits solo de formato, squash de historia previa, cambios funcionales mezclados con documentacion y refactorizaciones no relacionadas.

## CI/CD propuesta

Jobs futuros minimos:

- `backend-tests`: implementado en H1; instala backend, levanta PostgreSQL de CI y ejecuta pytest.
- `frontend-build`: implementado en H1; `npm ci` y `npm run build`.
- `alembic-check`: implementado en H1; valida heads, upgrade head y migracion desde base vacia.
- `openapi-check`: implementado en H1; genera OpenAPI y valida JSON con operationIds unicos. Ausencia profunda de campos sensibles queda para H2.
- `docker-build`: implementado en H1; construye imagen backend/frontend sin publicar.
- `smoke-test`: implementado en H1 como smoke minimo local/CI para `/health`, `/ready` y catalogo; login por rol y flujo basico quedan para H5.

Pull request: ejecutar `backend-tests`, `frontend-build`, `alembic-check` y `openapi-check`.

Merge a `staging`: construir imagenes, desplegar staging, ejecutar smoke tests y hacer rollback si falla readiness/smoke.

Promocion a `main`: aprobacion manual, deploy produccion, migracion controlada con backup previo, verificacion y rollback si falla.

## Estrategia de testing futura

- Unitarios: servicios de dominio, validadores, permisos y transiciones.
- Integracion API: routers con DB real de test y roles.
- Contratos: OpenAPI, schemas publicos, ausencia de secretos y campos internos.
- E2E: navegador real para flujos criticos.
- Smoke: checks post-deploy rapidos.
- Performance: busqueda, disponibilidad, reserva, pagos y dashboards.
- Seguridad: auth/authz negativa, rate limiting, webhooks, dependencias.
- Migraciones: upgrade desde cero y desde snapshots representativos.
- Restore: backup/restore en base aislada con evidencia.

E2E criticos priorizados:

```text
login -> disponibilidad -> reserva -> pago fake -> confirmacion
reserva -> Mercado Pago sandbox -> Webhook -> confirmacion
pago aprobado -> refund -> reconcile
reserva confirmada -> Meet -> Calendar -> notificacion
```

No se elige herramienta E2E en esta fase.

## Fases

| Fase | objetivo | alcance | fuera de alcance | dependencias | criterios de entrada | criterios de salida | riesgos | validaciones | commit esperado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H0 - Baseline productivo | Dejar staging desplegable, seguro y reproducible. | Configuracion por ambiente, `.env.example`, validaciones startup, staging seguro, documentacion operativa. | CI completa, E2E, integraciones productivas, refactors. | hosting, dominio, TLS, secret manager, PostgreSQL staging. | `staging` limpio, MVP aprobado, checklist staging. | staging con `APP_ENV=staging`, secrets externos, CORS cerrado, docs decididas, seed demo deshabilitado si publico, health/ready OK. | configuracion incompleta, CORS incorrecto, credenciales demo activas. | `/health`, `/ready`, migraciones, smoke manual minimo. | `chore(hardening): prepare staging baseline` |
| H1 - CI y calidad automatizada | Bloquear regresiones basicas. | backend tests, frontend build, migraciones, OpenAPI, Docker build, smoke minimo y documentacion CI. | deploy automatico, registry push, SAST profundo, E2E extensa. | H0, runner GitHub Actions, PostgreSQL CI. | H0 documentado y validado localmente. | workflow implementado, validacion local proporcional y evidencia remota pendiente tras push/PR. | primera corrida remota puede revelar diferencias de runner o Docker Compose. | push a `codex/**`, PR de prueba y pipeline completo. | `chore(ci): establish automated quality gates` |
| H2 - Seguridad y secretos | Reducir riesgos de auth, permisos, secretos y endpoints sensibles. | auth/authz, secretos, CORS, headers, rate limiting, webhooks, pagos, dependencias. | rediseño multi-tenant completo, MFA salvo decision explicita. | H1, owners secretos, politica seguridad. | CI minima disponible. | pruebas negativas por rol, SCA inicial, hardening webhooks/rate limit definido. | cambios de auth pueden afectar sesiones. | pytest, OpenAPI, permisos, logs sin secretos. | `chore(hardening): strengthen security baseline` |
| H3 - Observabilidad y operacion | Hacer diagnosticables staging y piloto. | logs estructurados, correlation IDs, metricas, alertas, health/readiness, runbooks. | tracing distribuido avanzado. | plataforma logs/metricas. | staging desplegable. | dashboards minimos, alertas de 5xx/DB/pagos/webhooks y runbooks. | ruido de alertas o PII en logs. | simulacion de errores controlados. | `chore(hardening): add operational observability baseline` |
| H4 - Base de datos y recuperacion | Proteger datos y migraciones. | backups, restore, migraciones seguras, rollback, retencion, mantenimiento. | alta disponibilidad avanzada. | PostgreSQL staging, almacenamiento backup. | DB staging creada. | backup automatico, restore probado, runbook migracion/rollback. | restore incompleto o migraciones no reversibles. | restore en base aislada y smoke posterior. | `docs(ops): define database backup and restore runbooks` |
| H5 - Testing avanzado | Cubrir flujos reales antes de piloto/produccion. | integracion sandbox, E2E, smoke, regresion, performance, carga. | automatizar todos los casos exploratorios. | H1, H0, cuentas sandbox, fixtures. | CI baseline y staging estable. | E2E criticos automatizados, smoke post-deploy y pruebas sandbox documentadas. | flakiness por proveedores externos. | ejecucion repetible en CI/staging. | `test(e2e): cover critical booking and payment flows` |
| H6 - Frontend y experiencia | Mejorar confiabilidad visual y uso en dispositivos reales. | responsive, accesibilidad, bundle, estados de error, UX critica. | rediseño completo o cambios amplios de producto. | H5 parcial, matriz de vistas/viewports. | flujos criticos estables. | auditoria responsive, WCAG basica, chunking medido y estados de error revisados. | cambios visuales pueden introducir regresiones. | build, capturas por viewport, axe/checklist, E2E criticos. | `fix(frontend): harden critical responsive and accessibility flows` |
| H7 - Piloto y produccion | Ejecutar piloto controlado y preparar promocion a produccion. | staging desplegado, usuarios piloto, integraciones reales controladas, checklist produccion, promocion a `main`. | nuevas funcionalidades no criticas. | H0-H6, aprobacion producto/legal/operacion. | gates staging y piloto cumplidos. | piloto monitoreado, incidentes controlados, aprobacion legal/seguridad y checklist produccion completo. | soporte insuficiente, fallos integraciones, decisiones fiscales pendientes. | smoke, E2E, backups/restore, alertas, carga basica, rollback probado. | `chore(release): prepare production promotion checklist` |

## Decisiones de alcance

Antes de staging real debe resolverse: configuracion de ambiente, secretos, CI basica, despliegue reproducible, backups, logs, smoke tests, HTTPS, dominio y variables productivas separadas.

Antes de piloto debe resolverse: monitoreo, soporte, restore probado, integraciones sandbox, privacidad, flujos E2E criticos y operacion de pagos/refunds.

Antes de produccion debe resolverse: seguridad profunda, integraciones productivas, cumplimiento legal, performance, alertas, continuidad, rollback probado y aprobacion manual.
