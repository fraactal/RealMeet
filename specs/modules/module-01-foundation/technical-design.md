# Diseno tecnico del Modulo 1

## Flujo de arranque objetivo

```text
PostgreSQL inicia
-> healthcheck de PostgreSQL
-> backend espera DB con timeout
-> backend ejecuta Alembic
-> backend ejecuta seed idempotente
-> backend inicia FastAPI
-> /health responde
-> /ready valida DB y configuracion critica
-> frontend inicia y consume VITE_API_URL
```

## Configuracion

Backend usa `pydantic-settings` en `app/core/config.py`. Las variables obligatorias son `SECRET_KEY` y `DATABASE_URL`. Las variables opcionales tienen defaults locales seguros para desarrollo. `CORS_ORIGINS` acepta JSON o CSV.

Frontend usa `VITE_API_URL` desde `import.meta.env`.

## Entorno

Se mantienen tres ejemplos:

- `.env.example`: variables para Docker Compose desde la raiz.
- `backend/.env.example`: variables para ejecutar backend localmente.
- `frontend/.env.example`: variables para ejecutar frontend localmente.

No se versionan `.env` reales.

## Docker Compose

Se mantienen servicios `db`, `backend`, `frontend`, puertos conocidos y volumen nombrado del proyecto. El backend sigue dependiendo del healthcheck de PostgreSQL y ademas conserva espera interna de DB para robustez.

## Migraciones

`app.bootstrap` ejecuta `alembic upgrade head` despues de `wait_for_database`. Alembic toma `DATABASE_URL` desde settings en `alembic/env.py`.

## Seed

El seed debe ser idempotente por entidad critica, no solamente por existencia del admin. Debe crear o reutilizar usuarios demo, categorias, especialidades, perfil profesional, relaciones y disponibilidad sin duplicar y sin registrar contrasenas.

## Health y readiness

`/health` valida proceso vivo y no depende de servicios externos. `/ready` valida DB y que settings criticos hayan cargado, sin depender de SMTP ni proveedores externos.

## Logs

Los logs pueden mostrar ambiente, host, puerto, CORS y resumen de DB sin password. No deben mostrar `SECRET_KEY`, passwords, tokens ni URLs completas con credenciales.

## Validacion

Se prioriza:

1. inspeccion estatica;
2. `docker compose config` o `docker-compose config`;
3. arranque Docker si el entorno lo permite;
4. endpoints health/ready/login/professionals;
5. validacion runtime de `REM-P0-001` si hay datos suficientes.
