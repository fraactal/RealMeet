# H1 CI y calidad automatizada

## Alcance

H1 implementa una CI minima para validar cambios antes de integrar ramas. No despliega, no publica imagenes y no usa secretos productivos.

## Jobs implementados

- `backend-tests`: ejecuta `pytest` completo con PostgreSQL efimero y providers fake/mock.
- `frontend-build`: ejecuta `npm ci` y `npm run build` con `VITE_API_URL` ficticia local.
- `alembic-check`: valida head unico, aplica migraciones desde base limpia y compara `current` contra `head`.
- `openapi-check`: genera OpenAPI importando FastAPI, valida JSON y verifica `operationId` unicos.
- `docker-build`: construye imagen backend y frontend sin push a registry.
- `smoke-test`: levanta `docker-compose.ci.yml` con nombre de proyecto aislado, valida `/health`, `/ready` y `GET /api/v1/categories`, muestra logs si falla y detiene servicios al finalizar.

## Hallazgos H1 atendidos

| hallazgo | estado anterior | cambio H1 | evidencia | estado final |
| --- | --- | --- | --- | --- |
| TD-006 | `planned`: CI minima ausente | Workflow CI baseline con seis jobs y caches pip/npm | `.github/workflows/ci.yml` | mitigated, pending remote evidence |
| TD-005 | `mitigated-h0`: smoke local/scriptable sin CI | Smoke automatizado como job dependiente de gates criticos | `.github/workflows/ci.yml`, `docker-compose.ci.yml`, `scripts/ci/smoke.sh` | mitigated, pending remote evidence |
| TD-007 | `documented`: sin lint/tests frontend | CI ejecuta build real y documenta que no existen lint/tests frontend | `frontend/package.json`, `docs/development/continuous-integration.md` | accepted |

## Evidencias locales

H0 pendiente fue validado localmente con Docker antes de implementar H1:

- `docker-compose up --build -d`: backend/frontend construidos y stack healthy.
- `docker-compose exec -T backend pytest tests/test_config.py tests/test_health.py`: 15 passed, 1 warning conocido de `passlib/crypt`.
- `Invoke-RestMethod -Uri http://localhost:18000/health`: `status=ok`, `environment=docker`.
- `Invoke-RestMethod -Uri http://localhost:18000/ready`: `status=ready`, `database=ok`, `configuration=ok`.
- `docker-compose exec -T frontend npm run build`: build correcto, warning conocido por chunk mayor a 500 kB.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-staging.ps1`: smoke H0 correcto.

La evidencia remota de H1 queda pendiente hasta que GitHub Actions ejecute el workflow en la rama publicada o en un PR.

## Validaciones H1 locales

- `docker-compose exec -T backend pytest`: 277 passed, 1 warning conocido de `passlib/crypt`.
- Alembic en base limpia `realmeet_h1_ci_quality`: head unico `20260719_0024`, `upgrade head` correcto y `current=head`.
- `docker run --rm ... python scripts/ci/check_openapi.py`: OpenAPI valido, 233 operaciones, sin `operationId` duplicados.
- `docker-compose config`: correcto.
- `docker-compose -f docker-compose.yml -f docker-compose.staging.yml config`: correcto.
- `docker-compose -f docker-compose.ci.yml config`: correcto.
- `docker build -t realmeet-backend:h1-ci ./backend`: correcto.
- `docker build -t realmeet-frontend:h1-ci ./frontend`: correcto.
- `bash scripts/ci/smoke.sh` con `COMPOSE_PROJECT_NAME=realmeet_ci_local2`: `/health`, `/ready` y `GET /api/v1/categories` correctos; servicios detenidos por el trap.
- Sintaxis YAML: no se pudo validar localmente con parser dedicado porque no hay PyYAML ni Ruby disponibles; queda pendiente de carga por GitHub Actions.

## Limitaciones

- No hay lint ni tests frontend definidos; H1 no crea scripts vacios.
- Los jobs usan servicios efimeros y fakes/mocks; no validan proveedores externos reales.
- `smoke-test` valida endpoints minimos, no flujos E2E completos.
- No hay deploy ni smoke post-deploy contra staging real.
- SCA/dependencias queda para H2.

## Riesgos

- Primera corrida remota puede revelar diferencias de Docker Compose o red en GitHub-hosted runners.
- Suite backend completa puede exponer tests dependientes de orden o de datos locales.
- Smoke CI usa seed demo en entorno aislado; no equivale a staging publico.

## Pendientes

- Abrir PR hacia `staging` para obtener evidencia remota por job.
- H2 debe sumar seguridad/SCA y pruebas negativas auth/authz.
- H5 debe ampliar smoke/E2E a flujos criticos de reserva, pagos e integraciones sandbox.

## Relacion con H2

H2 puede construir sobre este pipeline para agregar SCA, controles de secretos, auditoria auth/authz, hardening de webhooks y dependencias sin redisenar la base de CI.
