# Modulo 9: Hardening tecnico y preparacion segura para staging

## Identificador

`M9-TECH-HARDENING`

## Contexto

El Modulo 8 cerro el MVP funcional para desarrollo local y demo controlada. Persistian riesgos tecnicos antes de staging: secretos placeholder, Swagger siempre activo, ausencia de rate limiting, falta de headers HTTP, Dockerfiles root, seed demo automatico, falta de backup/restore documentado y vulnerabilidades npm conocidas.

## Objetivo

Reducir riesgos tecnicos principales antes de un despliegue a staging, sin agregar funciones comerciales o clinicas nuevas y sin realizar despliegue.

## Alcance

- Configuracion por entorno.
- Validacion de secretos en staging/production.
- CORS explicito y sin wildcard.
- Headers HTTP de seguridad basicos.
- Rate limiting basico en memoria para login y creacion de reservas.
- Swagger/OpenAPI configurable.
- Seed demo configurable por entorno.
- Dockerfiles con usuario no root cuando es viable.
- `.dockerignore` para backend/frontend.
- Documentacion de backup y restauracion PostgreSQL.
- Registro de riesgos residuales.
- Pruebas minimas.

## Exclusiones

- Cookies HttpOnly, CSRF y rediseño de auth.
- Redis o rate limiter distribuido.
- HTTPS, dominio, WAF, SIEM, Kubernetes, CI/CD o cloud.
- SAST/SCA completo, Trivy, pentesting, carga o estres.
- Funcionalidades clinicas, pagos, WhatsApp, Google Meet, Zoom o MFA.

## Riesgos reales confirmados

| Riesgo | Estado previo | Mitigacion M9 |
| --- | --- | --- |
| Secretos placeholder en staging | No rechazados | `Settings` rechaza secretos cortos/placeholders en staging/production. |
| CORS wildcard | No validado explicitamente | `Settings` rechaza `*` y origenes mal formados. |
| Swagger siempre activo | Siempre expuesto | `ENABLE_DOCS` controla OpenAPI/docs/redoc. |
| Sin headers de seguridad | Ausente | Middleware agrega headers basicos y no-store en rutas sensibles. |
| Sin rate limiting | Ausente | Middleware en memoria para login y reservas. |
| Seed demo siempre ejecutado | Siempre desde bootstrap | `ENABLE_DEMO_SEED` con default local; production no permite true. |
| Docker root | Dockerfiles sin usuario no root | Backend `appuser`; frontend `node`. |
| Build context amplio | Sin `.dockerignore` | `.dockerignore` backend/frontend agregados. |
| Backups no documentados | Ausente | README y checklist M9 documentan `pg_dump`/`pg_restore`. |

## Resultado esperado

Staging queda tecnicamente mas seguro y configurable, pero no listo para produccion ni uso clinico real.
