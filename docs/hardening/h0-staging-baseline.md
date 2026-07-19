# H0 staging baseline

H0 entrega una base reproducible para validar una configuracion equivalente a staging sin desplegar cloud, sin crear infraestructura y sin tocar datos reales. El objetivo es que staging falle temprano cuando falten controles criticos y que las validaciones estaticas sean repetibles.

## Controles incluidos

- `APP_ENV=staging` activa validaciones estrictas de configuracion.
- `DEBUG=true` se rechaza en staging/production.
- `ENABLE_DOCS=true` se rechaza en staging/production.
- `ENABLE_DEMO_SEED=true` se rechaza en staging/production.
- `SECRET_KEY` placeholder o menor a 32 caracteres se rechaza en staging/production.
- `CORS_ORIGINS=*` se rechaza siempre.
- `CORS_ORIGINS` con localhost se rechaza en staging/production, salvo `STAGING_ALLOW_LOCALHOST=true` para validacion local equivalente.
- `EMAIL_MODE=smtp` exige `SMTP_HOST`.
- Google OAuth solo se valida cuando alguna variable OAuth esta configurada; en ese caso debe estar completo.
- WhatsApp Cloud solo exige secretos operativos cuando `WHATSAPP_CLOUD_ENABLED=true`.
- `LOG_LEVEL` controla logging estructurado JSON a stdout.

## Archivos principales

- `.env.staging.example`: plantilla sin secretos reales para staging.
- `docker-compose.staging.yml`: override para renderizar una configuracion equivalente a staging.
- `scripts/smoke-staging.ps1`: smoke minimo contra `/health` y `/ready`.
- `docs/deployment/staging-configuration.md`: guia operativa de configuracion staging.

## Validacion acotada

Ejecutar inicialmente sin levantar Docker:

```powershell
git diff --check
cd backend
pytest tests/test_config.py tests/test_health.py
cd ..\frontend
npm run build
cd ..
docker-compose config
docker-compose -f docker-compose.yml -f docker-compose.staging.yml config
```

Cuando exista una instancia local o staging ya levantada, ejecutar:

```powershell
$env:REALMEET_BASE_URL="http://localhost:18000"
.\scripts\smoke-staging.ps1
```

## Fuera de alcance H0

- No despliega cloud, DNS, TLS ni base administrada.
- No automatiza backups ni restore.
- No crea CI/CD ni smoke post-deploy automatico.
- No valida integraciones reales productivas.
- No ejecuta suites E2E ni pruebas de performance.
