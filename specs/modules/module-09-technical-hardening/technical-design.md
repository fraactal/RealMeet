# Diseno tecnico del Modulo 9

## Settings

Se extiende `Settings` sin renombrar variables existentes:

- `DEBUG`
- `ENABLE_DOCS`
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_MAX_REQUESTS`
- `ENABLE_DEMO_SEED`

`APP_ENV` acepta `development`, `docker`, `test`, `staging`, `production` y `prod`. Staging y production rechazan `SECRET_KEY` placeholder o menor a 32 caracteres. Production rechaza `ENABLE_DEMO_SEED=true`.

## CORS

`CORS_ORIGINS` conserva soporte JSON o CSV. Ahora rechaza `*` y valores que no sean origenes `http`/`https` explicitos. No se hardcodean dominios futuros.

## Headers HTTP

`SecurityHeadersMiddleware` agrega:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Cache-Control: no-store` y `Pragma: no-cache` en rutas sensibles.

No se agrega CSP estricta porque puede romper Swagger/Vite sin una revision dedicada.

## Rate limiting

`InMemoryRateLimitMiddleware` aplica limites configurables a:

- `POST /api/v1/auth/login`
- `POST /api/v1/appointments`

El limite usa IP cliente, metodo y path. Devuelve `429` con `Retry-After`.

Limitacion: es en memoria y solo sirve para una instancia. Produccion multi-instancia requiere Redis, gateway o WAF.

## Swagger/OpenAPI

`ENABLE_DOCS` controla `openapi_url`, `docs_url` y `redoc_url`. Si no se define:

- development/docker/test/staging: habilitado por defecto;
- production/prod: deshabilitado por defecto.

## Seed demo

`ENABLE_DEMO_SEED` controla si `app.bootstrap` ejecuta el seed. Si no se define:

- development/docker/test: habilitado;
- staging/production: deshabilitado.

## Docker

- Backend crea usuario `appuser` y ejecuta como no root.
- Frontend ejecuta como usuario `node`.
- Se agregan `.dockerignore` para excluir envs, caches, dumps, logs, builds y claves.

## Logs

No se agregan logs de Authorization, JWT, passwords ni hashes. La URL de base de datos se mantiene redactada por `database_summary`. Se documenta que `logger.debug` de email body no debe habilitarse en staging/productive sin redaccion adicional.
