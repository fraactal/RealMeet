# Spec - H0 staging baseline

## Contexto

RealMeet tiene el MVP funcional cerrado e integrado en `staging`. La planificacion de hardening identifica como bloqueadores iniciales TD-001 a TD-005: staging real, secretos, exposicion publica/CORS/docs, backups/restore y smoke tests. H0 prepara una base tecnica reproducible para validar una configuracion equivalente a staging, sin desplegar ni iniciar H1-H7.

## Objetivo

Establecer una configuracion base para staging real que falle temprano ante valores inseguros, documente variables y comandos operativos, mantenga compatibilidad local y permita validar health/readiness/smoke de forma acotada.

## Alcance

- Endurecer settings backend para `staging` y `production`.
- Documentar y templatar variables de staging sin secretos reales.
- Mantener providers externos opcionales y validar solo cuando esten habilitados o configurados como politica activa.
- Agregar un override `docker-compose.staging.yml` para renderizar una configuracion local equivalente a staging.
- Documentar migraciones, health, readiness, smoke minimo y comandos prohibidos.
- Actualizar TD-001 a TD-005 con evidencia real de H0.

## Fuera de alcance

- Despliegue cloud, Terraform, CI/CD completo, GitHub Actions, E2E extensos, performance, pentesting, upgrades masivos, colas/workers, backups automatizados, restore automatizado, integraciones productivas reales, cobros reales, responsive/accesibilidad global, cambios de reglas de negocio, merge, tag o deploy.

## Requisitos funcionales

- Desarrollo local debe seguir funcionando con `.env.example`.
- Staging debe usar `APP_ENV=staging`, `DEBUG=false`, `ENABLE_DOCS=false`, `ENABLE_DEMO_SEED=false` y CORS explicito.
- Frontend debe tomar la URL de API desde `VITE_API_URL`; no debe recibir secretos.
- `/health` debe indicar proceso vivo.
- `/ready` debe validar configuracion critica y base de datos.

## Requisitos tecnicos

- `docker-compose.staging.yml` debe reutilizar `docker-compose.yml`, mantener healthchecks y no eliminar volumenes.
- Los scripts operativos, si existen, deben usar `docker-compose`, detenerse ante errores y evitar acciones destructivas.
- La validacion debe ser acotada: `git diff --check`, tests especificos de configuracion/health/readiness, build frontend y `docker-compose config`.

## Requisitos de seguridad

- No incluir secretos reales en plantillas ni compose.
- Rechazar secretos placeholder en `staging/production`.
- Rechazar CORS wildcard y configuraciones locales en staging real, salvo modo local equivalente explicitamente habilitado.
- Validar SMTP, Google Meet y WhatsApp solo cuando esten habilitados o seleccionados.
- Configurar `LOG_LEVEL` sin imprimir tokens, passwords ni payloads sensibles.

## Criterios de aceptacion

- TD-001 a TD-005 quedan resueltos, mitigados o diferidos con justificacion.
- Existe guia de configuracion staging.
- Staging falla claramente ante configuracion critica invalida.
- Compose staging puede renderizarse sin secretos reales.
- Build frontend no depende de localhost hardcodeado para staging.
- Validaciones acotadas pasan.

## Archivos esperados

- `specs/hardening/h0-staging-baseline/spec.md`
- `.env.staging.example`
- `docker-compose.staging.yml`
- `docs/hardening/h0-staging-baseline.md`
- `docs/deployment/staging-configuration.md`
- cambios acotados en settings/logging/frontend/env docs si corresponde.

## Estrategia de validacion

1. Tests especificos de settings y health/readiness.
2. `npm run build` en `frontend`.
3. `docker-compose config`.
4. `docker-compose -f docker-compose.yml -f docker-compose.staging.yml config`.
5. `git diff --check`.

La validacion integrada con servicios queda condicionada a que las variables de staging local esten preparadas y no exista riesgo para datos locales.

## Riesgos

- Staging cloud real sigue requiriendo infraestructura, dominio, TLS y secretos externos.
- Backups automatizados y restore probado quedan para H4.
- Smoke automatizado en CI queda para H1; H0 solo entrega script/manual local.

## Rollback

Revertir el commit H0 restaura la configuracion anterior. No hay migraciones ni cambios de datos en esta fase. No se eliminan volumenes ni recursos.

## Relacion con TD-001 a TD-005

- TD-001: mitigado con baseline reproducible y documentacion de staging.
- TD-002: mitigado con fail-fast y plantillas sin secretos reales.
- TD-003: mitigado con URLs publicas, CORS explicito, docs/seed deshabilitados y compose staging.
- TD-004: diferido parcialmente; H0 documenta backup/restore manual y deja automatizacion para H4.
- TD-005: mitigado con smoke minimo local; automatizacion CI queda para H1.

## Dependencias hacia H1

H1 debe automatizar `backend-tests`, `frontend-build`, `alembic-check`, `openapi-check` y smoke post-deploy. H0 no crea workflows.

## Decisiones y limitaciones aceptadas

- Se mantiene monolito modular y Docker Compose local.
- No se vuelven obligatorias integraciones opcionales.
- Se permite staging local equivalente con localhost solo mediante bandera explicita.
- No se introducen nuevos proveedores ni dependencias.
