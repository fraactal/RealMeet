# Continuous integration

## Cuando se ejecuta

El workflow `.github/workflows/ci.yml` se ejecuta en:

- `pull_request` hacia `staging`.
- `pull_request` hacia `main`.
- `push` a ramas `codex/**`.
- `workflow_dispatch` manual.

No usa `pull_request_target`, no despliega y no consume secretos productivos.

## Jobs

| job | valida | notas |
| --- | --- | --- |
| `backend-tests` | `pytest` backend completo | Usa PostgreSQL 16 efimero y variables `APP_ENV=test` |
| `frontend-build` | `npm ci` y `npm run build` | Usa `VITE_API_URL=http://localhost:18000` ficticia |
| `alembic-check` | head unico, `upgrade head`, `current == head` | Usa base PostgreSQL limpia del job |
| `openapi-check` | OpenAPI JSON y `operationId` unicos | No requiere servicios externos reales |
| `docker-build` | Dockerfile backend/frontend compilan | No publica imagenes |
| `smoke-test` | `/health`, `/ready`, `GET /api/v1/categories` | Levanta `docker-compose.ci.yml` aislado y detiene servicios al finalizar |

`smoke-test` depende de los otros cinco jobs.

## Variables de CI

Las variables son ficticias y seguras para CI:

- `SECRET_KEY=ci-...` con longitud suficiente.
- `DATABASE_URL` contra PostgreSQL efimero.
- `CORS_ORIGINS` local explicito.
- `EMAIL_MODE=log`.
- `DEFAULT_MEETING_PROVIDER=mock`.
- `WHATSAPP_CLOUD_ENABLED=false`.
- `RATE_LIMIT_ENABLED=false` para evitar flakiness en tests/smoke.

No se usan `secrets.*` ni credenciales productivas.

## Reproduccion local

Backend:

```powershell
docker-compose exec -T backend pytest
```

Frontend:

```powershell
docker-compose exec -T frontend npm run build
```

Alembic dentro del contenedor backend:

```powershell
docker-compose exec -T backend alembic heads
docker-compose exec -T backend alembic current
```

OpenAPI, con dependencias backend instaladas en el entorno local:

```powershell
$env:APP_ENV="test"
$env:SECRET_KEY="local-test-secret-with-at-least-32-chars"
$env:DATABASE_URL="postgresql+pg8000://realmeet:realmeet@localhost:25432/realmeet"
$env:CORS_ORIGINS='["http://localhost:15173"]'
python scripts/ci/check_openapi.py
```

Compose render:

```powershell
docker-compose config
docker-compose -f docker-compose.yml -f docker-compose.staging.yml config
```

Smoke local H0:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-staging.ps1
```

Smoke CI local en Bash-compatible shell:

```bash
COMPOSE_PROJECT_NAME=realmeet_ci_local BACKEND_PORT=18080 FRONTEND_PORT=15180 POSTGRES_PORT=25433 CORS_ORIGINS=http://localhost:15180 bash scripts/ci/smoke.sh
```

## Interpretacion de fallos

- `backend-tests`: revisar assertion, migraciones pendientes o variables de test.
- `frontend-build`: revisar errores TypeScript/Vite; el warning de chunk grande es deuda conocida y no falla el build.
- `alembic-check`: revisar multiples heads o migracion que no aplica desde base limpia.
- `openapi-check`: revisar rutas sin `operationId` o duplicados generados por FastAPI.
- `docker-build`: revisar Dockerfile, lockfiles, dependencias o permisos de usuario.
- `smoke-test`: revisar logs que el job imprime automaticamente para `backend`, `frontend` y `db`.

## Reintentos

- En PR: usar re-run failed jobs desde GitHub Actions.
- En push a `codex/**`: empujar un nuevo commit o usar workflow manual.
- Localmente: corregir la causa y repetir solo el comando del job afectado.

## Lo que no hace

- No despliega staging ni produccion.
- No publica imagenes.
- No usa registry ni OIDC cloud.
- No ejecuta E2E extensos.
- No ejecuta SCA/dependency audit.
- No prueba integraciones reales externas.
- No crea lint/tests frontend inexistentes.

## Limpieza local segura

Para detener servicios locales sin borrar volumenes:

```powershell
docker-compose stop
```

Evitar `docker-compose down -v`, `docker volume prune`, `docker system prune` y comandos que borren volumenes.
