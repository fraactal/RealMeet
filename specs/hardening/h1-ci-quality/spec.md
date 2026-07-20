# Spec - H1 CI y calidad automatizada

## Contexto

H0 dejo una base reproducible para staging equivalente, con settings estrictos, plantillas de ambiente, compose staging y smoke minimo. H1 agrega gates automatizados para evitar que regresiones basicas lleguen a `staging` o `main` sin validacion previa.

## Objetivo

Implementar una integracion continua minima, reproducible y segura para validar backend, frontend, migraciones, contrato OpenAPI, build Docker y smoke minimo sin desplegar ni usar secretos productivos.

## Alcance

- Workflow GitHub Actions para PR hacia `staging` y `main`, push a `codex/**` y ejecucion manual.
- `docker-compose.ci.yml` para smoke aislado sin `container_name` fijo.
- Jobs `backend-tests`, `frontend-build`, `alembic-check`, `openapi-check`, `docker-build` y `smoke-test`.
- Scripts pequenos reutilizables para OpenAPI y smoke.
- Documentacion de uso, troubleshooting y evidencias H1.
- Actualizacion acotada de registros de hardening relacionados con H1.

## Fuera de alcance

- Deploy automatico, CD, OIDC cloud, registry push, secretos productivos, Terraform, Dependabot/Renovate, E2E extensa, performance, pentesting, observabilidad completa, backups/restore, cambios funcionales o deuda H2-H7.

## Requisitos

- Usar Python 3.12 y Node 22, alineados con Dockerfiles y stack actual.
- Instalar dependencias con `pip install -r requirements.txt` y `npm ci`.
- Usar PostgreSQL efimero de job para pruebas y migraciones.
- Ejecutar providers fake/mock y no depender de integraciones externas reales.
- Usar permisos minimos `contents: read`.
- No usar `pull_request_target` ni secretos productivos.
- No crear scripts vacios para lint/tests frontend inexistentes.

## Jobs CI

- `backend-tests`: instala backend, levanta PostgreSQL de servicio y ejecuta `pytest` completo.
- `frontend-build`: instala frontend con `npm ci` y ejecuta `npm run build`.
- `alembic-check`: valida head unico, aplica migraciones desde base limpia y compara `current` con `head`.
- `openapi-check`: importa FastAPI, genera OpenAPI JSON y falla ante `operationId` ausentes o duplicados.
- `docker-build`: construye imagen backend y frontend sin publicarlas.
- `smoke-test`: depende de los jobs anteriores, levanta un stack Compose aislado, valida `/health`, `/ready` y `GET /api/v1/categories`, muestra logs si falla y detiene servicios al finalizar.

## Dependencias entre jobs

`backend-tests`, `frontend-build`, `alembic-check`, `openapi-check` y `docker-build` corren en paralelo. `smoke-test` depende de todos ellos para evitar levantar el stack si un gate critico ya fallo.

## Estrategia de cache

- `actions/setup-python` cachea `pip` con `backend/requirements.txt`.
- `actions/setup-node` cachea `npm` con `frontend/package-lock.json`.
- Docker build usa cache local del runner sin push ni registry.

## Manejo de secretos

El workflow define secretos ficticios de CI en `env`. No usa `secrets.*`, no imprime tokens productivos y mantiene integraciones externas opcionales deshabilitadas.

## Estrategia Docker

`docker-build` verifica que ambos Dockerfiles compilen. `smoke-test` usa `docker-compose.ci.yml` con `COMPOSE_PROJECT_NAME` aislado y puertos CI dedicados. El script detiene servicios en `trap`; no elimina volumenes ni recursos externos.

## Criterios de aceptacion

- Workflow creado en `.github/workflows/ci.yml`.
- Jobs cubren backend, frontend, Alembic, OpenAPI, Docker build y smoke minimo.
- Scripts auxiliares son pequenos, sin secretos y ejecutables localmente.
- Documentacion H1 y guia CI existen.
- Registros de hardening H1 actualizados con evidencia implementada y pendiente remota.
- Validaciones locales proporcionales ejecutadas o documentadas con causa.

## Validaciones

- `git diff --check`.
- Sintaxis YAML si hay herramienta disponible.
- `pytest` backend mediante contenedor cuando sea viable.
- `npm run build` mediante contenedor cuando sea viable.
- Alembic head/upgrade/current sobre DB efimera cuando sea viable.
- `python scripts/ci/check_openapi.py`.
- `docker-compose config` y override staging.
- Build backend/frontend.
- Smoke local o CI con `/health`, `/ready` y endpoint API minimo.

## Riesgos

- Primera ejecucion remota puede revelar diferencias de runner, red o Docker Compose.
- Suite backend completa puede tardar mas que validaciones locales acotadas.
- Smoke usa seed demo en ambiente CI aislado; no representa staging publico.
- Frontend sigue sin lint/tests propios.

## Rollback

Revertir el commit H1 elimina workflow, scripts y documentos H1. No hay migraciones ni cambios de datos.

## Relacion con deuda tecnica

- TD-006 queda mitigado/implementado con pipeline CI baseline, pendiente evidencia remota verde.
- TD-005 avanza con smoke automatizado en CI, aunque smoke post-deploy real queda para H5/CD futuro.
- TD-007 queda documentado como limitacion: no se simula lint/tests frontend inexistentes.

## Dependencias hacia H2

H2 puede asumir una CI baseline para agregar SCA, pruebas negativas auth/authz, hardening de secretos, rate limiting centralizado y controles de seguridad mas profundos.
