# Revision integral pre-MVP

## Resumen ejecutivo

Estado general: aprobado para integrar a `staging`.

La revision se ejecuto sobre `codex/pre-mvp-integration-review`, creada desde `bce3ee9 chore(integrations): finalize Google Workspace module`.

Resultados:

- Backend: `230 passed, 1 warning`.
- Frontend: build productivo correcto.
- Migraciones: un solo head `20260718_0020`; base actual en head; migracion desde base vacia aislada correcta.
- API: OpenAPI valido en `/api/v1/openapi.json`; 158 paths, 185 schemas, 199 operationIds sin duplicados.
- Health: `/health` responde `200`.
- Readiness: `/ready` responde `200`.
- Docker: `backend`, `frontend` y `db` activos y healthy.

Flujos validados por suite y revision:

- autenticacion y roles;
- catalogo, disponibilidad y reservas;
- Google Meet con fakes;
- WhatsApp y email con fakes;
- webhooks y n8n;
- calendarios externos y Google Calendar con fakes;
- Google Sheets;
- Google Docs y Drive;
- automatizacion documental;
- permisos administrativos, profesionales y cliente.

## Correcciones bloqueantes aplicadas

### FIX-001 - Test unitario de disponibilidad no declaraba que cubria solo slots internos

Problema: `tests/test_availability.py::test_availability_slots_exclude_blocked_interval` fallaba en suite completa porque el test usaba un `FakeSession` sin `.get()`, mientras `AvailabilityService.list_slots` ahora filtra por calendarios externos por defecto.

Impacto: la suite completa fallaba e impedia aprobar la integracion a staging.

Causa: fixture unitario desactualizado frente al contrato integrado posterior al Modulo 15.

Solucion aplicada: el test llama `list_slots(..., include_external=False)` para declarar que cubre solo bloqueos internos.

Tests asociados:

- `docker-compose exec -T backend pytest -q tests/test_availability.py::test_availability_slots_exclude_blocked_interval -ra`
- `docker-compose exec -T backend pytest -q -ra`

## Deuda tecnica documentada

### Backend

#### PMVP-BE-001 - Warning passlib/crypt

Severidad orientativa: baja.

Descripcion: pytest reporta `DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13`.

Impacto: no afecta Python 3.12 actual, pero debe revisarse antes de migrar runtime.

Recomendacion futura: actualizar estrategia de hashing o dependencia compatible con Python 3.13.

Bloquea staging: no.

### Frontend

#### PMVP-FE-001 - Scripts frontend sin test ni lint

Severidad orientativa: media.

Descripcion: `frontend/package.json` define `dev`, `build` y `preview`, pero no `test` ni `lint`.

Impacto: validacion frontend depende del build TypeScript/Vite y pruebas manuales.

Recomendacion futura: agregar lint y tests de componentes/flujos criticos.

Bloquea staging: no.

### Seguridad

#### PMVP-SEC-001 - JWT en localStorage

Severidad orientativa: media.

Descripcion: el frontend conserva el token en `localStorage`.

Impacto: una vulnerabilidad XSS podria exfiltrar el token.

Recomendacion futura: migrar a cookies HttpOnly/SameSite y revisar CSRF.

Bloquea staging: no.

#### PMVP-SEC-002 - Secretos productivos pendientes

Severidad orientativa: media.

Descripcion: `.env.example` usa placeholders locales y documenta variables sensibles vacias o de ejemplo.

Impacto: staging real requiere secretos fuertes y gestionados fuera de Git.

Recomendacion futura: usar gestor de secretos, rotacion y checklist previo a despliegue.

Bloquea staging: no.

### Arquitectura

#### PMVP-ARCH-001 - OAuth Google administrativo/global

Severidad orientativa: media.

Descripcion: Workspace, Calendar, Meet, Sheets, Drive y Docs reutilizan un OAuth Google administrativo/global.

Impacto: suficiente para MVP/staging, pero limita escenarios multi-tenant avanzados.

Recomendacion futura: definir OAuth por organizacion o profesional segun modelo comercial.

Bloquea staging: no.

#### PMVP-ARCH-002 - Operaciones externas sincronicas

Severidad orientativa: media.

Descripcion: Sheets, Docs, retry y reconcile se ejecutan de forma sincronica y manual.

Impacto: operaciones lentas pueden afectar UX administrativa.

Recomendacion futura: introducir workers/colas y reintentos automaticos controlados.

Bloquea staging: no.

### Dependencias

#### PMVP-DEP-001 - Sin SCA/auditoria de dependencias en flujo actual

Severidad orientativa: media.

Descripcion: no existe script de auditoria de dependencias en el proyecto o CI local.

Impacto: vulnerabilidades no bloqueantes pueden pasar sin reporte automatico.

Recomendacion futura: agregar SCA, `npm audit` controlado, Dependabot/Renovate o equivalente en CI.

Bloquea staging: no.

### Performance

#### PMVP-PERF-001 - Bundle Vite mayor a 500 kB

Severidad orientativa: baja.

Descripcion: build frontend reporta chunk JS de `614.29 kB`.

Impacto: carga inicial suboptima en conexiones lentas.

Recomendacion futura: code splitting y estrategia de chunks.

Bloquea staging: no.

### Responsive

#### PMVP-RESP-001 - Revision responsive no exhaustiva

Severidad orientativa: baja.

Descripcion: la revision pre-MVP no ejecuta auditoria responsive profunda ni capturas nuevas.

Impacto: pueden quedar ajustes visuales finos en vistas complejas.

Recomendacion futura: matriz responsive para landing, login, dashboards, integraciones y Workspace.

Bloquea staging: no.

### Accesibilidad

#### PMVP-A11Y-001 - Sin auditoria WCAG completa

Severidad orientativa: baja.

Descripcion: la validacion cubre errores bloqueantes de uso, pero no una auditoria WCAG completa.

Impacto: pueden quedar mejoras de foco, ARIA o contraste.

Recomendacion futura: incorporar axe/Playwright y checklist WCAG por flujos criticos.

Bloquea staging: no.

### Observabilidad

#### PMVP-OBS-001 - Observabilidad productiva pendiente

Severidad orientativa: media.

Descripcion: no hay tracing, metricas productivas ni alertas integradas.

Impacto: diagnostico en staging/productivo sera limitado.

Recomendacion futura: agregar logs estructurados, metricas, tracing y alertas.

Bloquea staging: no.

### Infraestructura

#### PMVP-INFRA-001 - Staging real pendiente de parametrizacion externa

Severidad orientativa: media.

Descripcion: Docker Compose local funciona, pero staging real requiere secretos, dominios, backups, CORS y politica de despliegue.

Impacto: no bloquea crear rama `staging`, pero si un despliegue productivo.

Recomendacion futura: pipeline CI/CD, backups, rollback, TLS y configuracion gestionada.

Bloquea staging: no.

### Testing

#### PMVP-TEST-001 - Sin E2E de navegador

Severidad orientativa: media.

Descripcion: los flujos criticos estan cubiertos por tests backend e integracion con fakes; no hay E2E completo de navegador.

Impacto: puede faltar cobertura de interacciones frontend reales.

Recomendacion futura: Playwright/Cypress para login, reserva, dashboard e integraciones.

Bloquea staging: no.

## Limitaciones aceptadas

- OAuth Google administrativo/global.
- Operaciones externas probadas con fakes.
- Ejecucion sincronica de Sheets.
- Limite de 1.000 reservas por ejecucion.
- Email sin adjuntos.
- Retry/reconcile manual.
- n8n dependiente de webhooks.
- Ausencia de workers.
- Ausencia de scheduler para integraciones externas.
- Ausencia de colas.
- Chunk Vite mayor a 500 kB.
- Sin sincronizacion bidireccional.
- Sin pruebas reales de proveedores externos.

## Recomendaciones futuras

- CI/CD con suite backend, build frontend y migraciones desde cero.
- E2E de flujos criticos.
- Hardening de autenticacion y migracion a cookies HttpOnly.
- Observabilidad productiva.
- Pruebas responsive y accesibilidad.
- Reduccion de bundle frontend.
- Gestion de secretos productivos.
- Backups y recuperacion.
- Rate limiting avanzado por usuario/IP y endpoints sensibles.
- Auditoria profunda de seguridad y dependencias.

## Decision

La revision aprueba integrar hasta Modulo 16 en `staging`, siempre que se mantengan documentadas las deudas no bloqueantes y no se inicie Modulo 17 en esta etapa.
