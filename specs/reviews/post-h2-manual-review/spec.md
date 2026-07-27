# Spec - Post-H2 manual review

## Objetivo

Cerrar la revision manual posterior a H0-H2 y corregir solo hallazgos reproducibles de preparacion local, dejando `staging` listo para iniciar H3 en una fase posterior.

## Alcance

- Corregir plantillas OAuth para que no generen configuracion parcial.
- Mantener validacion fail-fast de settings.
- Documentar evidencia manual post-H2.
- Clasificar respuestas 400/422 observadas durante revision manual.
- Ejecutar validaciones acotadas: `git diff --check`, `pytest tests/test_config.py -vv`, render Compose base/staging y carga de settings sin OAuth.

## Fuera de alcance

- H3 y observabilidad.
- Prometheus, Grafana, OpenTelemetry, Sentry o alertas.
- Backups/restore.
- E2E extensa, performance, responsive global o accesibilidad profunda.
- Cambios funcionales en pagos, WhatsApp, Google real o endpoints.
- Credenciales Google reales.
- Merge a `staging` o `main`, tag o despliegue.

## Evidencia manual

Se levanto Docker Compose local y se verifico PostgreSQL, migraciones, seed, backend, frontend, `/ready`, login de roles, rutas admin, perfil profesional, disponibilidad, reservas, confirmacion/cancelacion, pagos fake, reconcile/retry y redaccion parcial de logs de email.

## Hallazgo OAuth

Las plantillas incluian `GOOGLE_OAUTH_REDIRECT_URI` con un callback por defecto mientras client ID, secret y encryption key estaban vacios. Settings rechaza correctamente esa configuracion parcial. Las plantillas deben dejar OAuth completamente vacio por defecto y documentar callbacks como comentarios.

## Criterios de aceptacion

- `GOOGLE_OAUTH_CLIENT_ID=`, `GOOGLE_OAUTH_CLIENT_SECRET=`, `GOOGLE_OAUTH_REDIRECT_URI=` y `GOOGLE_TOKEN_ENCRYPTION_KEY=` pueden quedar vacios y settings carga con OAuth deshabilitado.
- Solo redirect configurado sigue siendo invalido.
- Los cuatro valores OAuth configurados juntos habilitan `google_oauth_configured`.
- `.env.example`, `backend/.env.example`, `.env.staging.example` y `docker-compose.staging.yml` no inducen configuracion OAuth parcial.
- No se agregan secretos reales.
- No se relaja el fail-fast.

## Validaciones

- `git diff --check`.
- `pytest tests/test_config.py -vv`.
- `docker-compose config`.
- `docker-compose -f docker-compose.yml -f docker-compose.staging.yml config`.
- Carga de `Settings` con valores locales de plantilla y OAuth vacio.

## Rollback

Revertir el commit `fix(config): align OAuth templates with fail-fast validation`. No requiere migraciones ni rollback de datos porque solo cambia plantillas, docs y pruebas de configuracion.

## Dependencias hacia H3

H3 puede asumir que `staging` parte con H0-H2 integrados y plantillas OAuth coherentes con fail-fast. Observabilidad, alertas, runbooks y mejoras de UX de errores deben implementarse en ramas H3/H6 separadas.