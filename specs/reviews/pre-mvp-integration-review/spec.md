# Revision pre-MVP e integracion a staging

## Objetivo

Validar integralmente RealMeet hasta el Modulo 16, corregir solo bloqueantes y preparar integracion a `staging`.

## Alcance

- Modulos 0-9: MVP funcional inicial.
- Modulo 10: UX/UI.
- Modulo 11: fundacion de integraciones.
- Modulo 12: Google Meet.
- Modulo 13: WhatsApp.
- Modulo 14: webhooks, n8n y automatizacion operativa.
- Modulo 15: calendarios externos y Google Calendar.
- Modulo 16: Google Workspace, Sheets, Docs y automatizacion documental.

## Fuera de alcance

- Modulo 17.
- Refactors amplios.
- Hardening exhaustivo.
- Optimizacion de performance.
- Redisenos UX.
- Actualizaciones masivas de dependencias.
- Despliegue.
- Merge a `main`.
- Tags.

## Estrategia de pruebas

- Docker Compose config y estado de servicios.
- Alembic current, heads, history y upgrade head.
- Migracion desde base vacia aislada.
- Suite backend completa.
- Build frontend.
- OpenAPI en `/api/v1/openapi.json`.
- Health y readiness.
- Revision acotada de permisos, secretos y contratos.

## Flujos criticos

- Autenticacion y roles.
- Catalogo, disponibilidad y reservas.
- Google Meet con fakes.
- WhatsApp y email con fakes.
- Webhooks y n8n.
- Calendarios externos.
- Google Sheets.
- Google Docs y Drive.
- Automatizacion documental.

## Criterios de aceptacion

- Suite backend completa pasa.
- Frontend compila.
- Alembic tiene un unico head.
- Base actual esta en head.
- Migraciones desde cero pasan en base temporal.
- `/health` y `/ready` responden correctamente.
- OpenAPI es valido.
- No hay exposicion directa de secretos.
- Hallazgos no bloqueantes documentados.
- Arbol Git limpio antes de integrar.

## Correcciones

Se corrigio el test unitario `test_availability_slots_exclude_blocked_interval` para desactivar explicitamente el filtrado externo (`include_external=False`) porque el test valida solo disponibilidad interna.

## Deuda documentada

La deuda futura queda en `docs/reviews/pre-mvp-integration-review.md`, separada por backend, frontend, seguridad, arquitectura, dependencias, performance, responsive, accesibilidad, observabilidad, infraestructura y testing.

## Resultado

Revision aprobada tras validaciones completas.

## Limitaciones

- Proveedores externos reales no se invocan.
- OAuth Google es administrativo/global.
- Operaciones externas son sincronicas o manuales.
- No hay workers, scheduler ni colas.
- Chunk Vite mayor a 500 kB.

## Decision de integracion

Crear commit `chore(core): complete pre-MVP integration review`, publicar `codex/pre-mvp-integration-review` y preparar `staging` sin tocar `main`.
