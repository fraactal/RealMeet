# Staging configuration

Esta guia describe la configuracion minima para validar RealMeet en un entorno equivalente a staging. No contiene secretos reales ni instrucciones de despliegue cloud.

## Variables obligatorias

Backend staging debe definir:

- `APP_ENV=staging`
- `DEBUG=false`
- `ENABLE_DOCS=false`
- `ENABLE_DEMO_SEED=false`
- `SECRET_KEY` fuerte, aleatorio y de 32+ caracteres
- `DATABASE_URL` apuntando a la base staging
- `CORS_ORIGINS` con origenes publicos exactos, sin wildcard
- `VITE_API_URL` apuntando al backend publico usado por frontend

Variables operativas recomendadas:

- `LOG_LEVEL=INFO`
- `RATE_LIMIT_ENABLED=true`
- `EMAIL_MODE=log` hasta configurar SMTP real
- `DEFAULT_MEETING_PROVIDER=mock` hasta habilitar una politica real

`STAGING_ALLOW_LOCALHOST=true` solo se permite para una validacion local equivalente. No debe usarse en un staging publico.

## Secretos

No guardar secretos reales en Git. `.env.staging.example` usa placeholders para que el proceso falle si se copia sin reemplazar:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `SMTP_PASSWORD`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_TOKEN_ENCRYPTION_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- `WHATSAPP_PHONE_HMAC_KEY`

## Render de Compose

Validar la configuracion base sin levantar servicios:

```powershell
docker-compose config
```

Validar el override staging sin levantar servicios:

```powershell
docker-compose --env-file .env.staging.example -f docker-compose.yml -f docker-compose.staging.yml config
```

Para una validacion local equivalente con localhost, crear un archivo local no commiteado con `STAGING_ALLOW_LOCALHOST=true`, `CORS_ORIGINS=["http://localhost:15173"]`, `VITE_API_URL=http://localhost:18000` y un `SECRET_KEY` fuerte.

## Health, readiness y smoke

- `/health` confirma que el proceso FastAPI responde.
- `/ready` valida configuracion critica y conexion a PostgreSQL.
- `scripts/smoke-staging.ps1` valida ambos endpoints contra `REALMEET_BASE_URL`.

Ejemplo:

```powershell
$env:REALMEET_BASE_URL="https://api.staging.realmeet.example"
.\scripts\smoke-staging.ps1
```

## Backup y restore manual

H0 no automatiza backups. Antes de exponer staging o correr migraciones con datos que deban conservarse:

1. Crear backup con `pg_dump` hacia almacenamiento fuera del repositorio.
2. Validar el dump con `pg_restore --list`.
3. Probar restore en una base aislada.
4. Registrar fecha, responsable, base origen, base destino y resultado.

No restaurar sobre una base activa sin backup previo, ventana de mantenimiento y rollback.

## Comandos prohibidos

No usar en staging ni en validaciones H0:

- `git reset --hard`
- `git clean`
- `docker-compose down -v`
- `docker volume prune`
- `docker system prune`
- `docker volume rm`

## Cierre H0

H0 se considera suficiente cuando pasan las validaciones acotadas, TD-001 a TD-005 quedan actualizados y existe evidencia de que el override staging renderiza sin secretos reales. Staging real sigue requiriendo infraestructura, dominio, TLS, secretos externos y backups automatizados.
