# Spec - H2 seguridad y secretos

## Contexto

H1 dejo CI remota verde en `codex/h1-ci-quality` con backend, frontend, Alembic, OpenAPI, Docker y smoke. H2 parte desde ese baseline para reducir riesgos de secretos, autenticacion, autorizacion y superficies sensibles antes de un piloto controlado.

Los hallazgos reales considerados desde `docs/hardening/technical-debt-register.md` son TD-002, TD-012, TD-013, TD-016, TD-017, TD-018, TD-019 y TD-026. H0 ya mitigo parcialmente TD-002, TD-003 y la configuracion staging; H1 ya mitigo TD-006 y TD-005.

## Objetivo

Establecer un baseline de seguridad reproducible para secretos, configuracion sensible, logging, CI y pruebas criticas, sin introducir funcionalidades de negocio ni proveedores cloud de secretos.

## Alcance

- Validaciones de configuracion sensible para staging/production.
- Redaccion defensiva de logs para tokens, passwords, firmas y cabeceras sensibles.
- Gate CI acotado para escaneo de secretos, configuracion sensible y auditoria frontend critica.
- Inventario de categorias de secretos sin valores reales.
- Modelo simple de amenazas y baseline de controles actuales.
- Actualizacion de registros de hardening solo para hallazgos H2.

## Fuera de alcance

- Secret manager cloud, Vault, OIDC cloud, rotacion real de credenciales, MFA, SSO, cookies HttpOnly, Redis, WAF, observabilidad completa, backups, E2E, DAST, pentesting, deploy, merge o H3.

## Hallazgos H2

- TD-002: gestion externa de secretos pendiente para staging.
- TD-012: rotacion de secretos de integraciones pendiente.
- TD-013: hardening operacional de webhooks pendiente.
- TD-016: JWT persistido en `localStorage`.
- TD-017: rate limiter en memoria no distribuido.
- TD-018: auditoria profunda de autorizacion pendiente.
- TD-019: SCA automatica no integrada.
- TD-026: warning `passlib/crypt` para Python 3.13.

## Activos protegidos

- JWT y `SECRET_KEY`.
- Credenciales de base de datos.
- Tokens OAuth Google y clave Fernet.
- Tokens WhatsApp/Meta, app secret y verify token.
- Tokens y secretos Mercado Pago.
- Secretos de webhooks salientes y n8n.
- Datos personales de usuarios, reservas, pagos, notificaciones y auditoria.
- Logs, respuestas API, UI administrativa y artefactos CI.

## Actores y superficies de ataque

- Usuario anonimo: login, registro, catalogo publico, disponibilidad y webhooks publicos.
- Cliente autenticado: reservas, pagos propios y perfil.
- Profesional autenticado: perfil, disponibilidad, reservas propias y metricas.
- Administrador: backoffice, integraciones, pagos, exports y configuracion.
- Proveedor externo: Google, WhatsApp, Mercado Pago, SMTP y n8n.
- Navegador: frontend, almacenamiento local del JWT y redirecciones de checkout.
- CI: workflow, caches, logs y scripts de validacion.

## Trust boundaries

- Navegador -> backend API.
- Backend -> PostgreSQL.
- Backend -> proveedores externos.
- Proveedores externos -> webhooks publicos.
- Backend -> webhooks salientes/n8n.
- GitHub Actions -> repo y servicios efimeros.
- Entorno runtime -> variables de entorno y referencias de secretos.

## Requisitos de seguridad

- No versionar secretos reales.
- Rechazar configuracion insegura en staging/production.
- Mantener JWT firmado con algoritmo explicito y expiracion acotada.
- Rechazar usuarios inactivos y roles insuficientes.
- Mantener headers de seguridad y CORS explicito.
- No imprimir tokens, passwords, firmas ni secretos en logs.
- Usar referencias `*_REFERENCE` o nombres de variables para integraciones.
- Firmar y deduplicar webhooks relevantes.
- Usar timeouts en llamadas HTTP externas.
- Mantener errores publicos sanitizados.

## Estrategia de secretos

H2 mantiene provision por variables de entorno para desarrollo, CI y staging local. Los valores reales deben residir fuera de Git en el proveedor de hosting o secret store futuro. Las integraciones guardan referencias a variables, no valores. La resolucion ocurre en backend y solo en memoria.

No se implementa un proveedor cloud especifico; eso queda condicionado a la plataforma de despliegue.

## Autenticacion y autorizacion

JWT usa `HS256`, `SECRET_KEY` externo, expiracion configurable y validacion de `sub`. Los usuarios inactivos se rechazan. Los routers usan dependencias por rol y tests de auth/authz existentes cubren casos criticos. H2 agrega limite de expiracion y mantiene deuda TD-016 para migrar almacenamiento de token fuera de `localStorage`.

## Webhooks y callbacks

WhatsApp valida verify token con comparacion segura, firma HMAC, tamano de body e idempotencia. Mercado Pago valida firma e idempotencia y consulta al proveedor antes de aplicar pagos. Webhooks salientes/n8n usan firmas HMAC, referencias de secretos y URLs validadas. Rate limiting especifico por proveedor/IP queda diferido hasta H3/H5 con proxy o gateway.

## Llamadas externas

WhatsApp y Mercado Pago usan `httpx` con timeouts. Webhooks salientes no siguen redirects y validan URLs. Google OAuth limita scopes y redirect URI configurado. No se realizan llamadas reales en tests ni CI H2.

## Logging seguro

El logging JSON redacta claves sensibles y H2 agrega redaccion de patrones sensibles en mensajes libres: bearer tokens, authorization, firmas, passwords, tokens, secrets, credentials y API keys.

## Frontend

El frontend solo expone `VITE_API_URL`. No debe recibir secretos. El JWT sigue en `localStorage` como deuda TD-016; se documenta riesgo residual y no se migra en H2 para evitar redisenar auth/CSRF. No se detecto uso de `innerHTML` o `dangerouslySetInnerHTML` en la inspeccion H2.

## CI

Se agrega `security-check` sin secretos productivos:

- `scripts/ci/secret_scan.py`.
- `scripts/ci/check_security_config.py`.
- `npm audit --audit-level=critical`.

No se usa `pull_request_target`, no se usan `secrets.*` y `permissions` permanece en `contents: read`.

## Criterios de aceptacion

- Mini-spec H2 creada.
- Inventario de secretos y threat model creados.
- Configuracion staging/production rechaza rate limiting deshabilitado y expiracion JWT fuera de rango.
- Logging sensible redacta valores en claves y mensajes.
- Gate CI H2 implementado y validado localmente.
- Tests especificos y suite completa pasan.
- No hay secretos reales conocidos en arbol ni patrones de alta confianza en historial.
- Registros H2 actualizados con evidencia real.

## Estrategia de pruebas

- `pytest tests/test_config.py tests/test_security_hardening.py -vv`.
- `pytest`.
- `python scripts/ci/secret_scan.py`.
- `python scripts/ci/check_security_config.py`.
- `npm audit --audit-level=critical`.
- Validaciones H1 existentes: frontend build, Alembic, OpenAPI, Docker config/build y smoke.

## Riesgos

- El escaneo de secretos es acotado y no reemplaza secret scanning del proveedor Git.
- `npm audit` queda bloqueando solo vulnerabilidades criticas; vulnerabilidades high existentes se mantienen documentadas.
- Rate limiting sigue en memoria y no protege multi-instancia.
- `localStorage` mantiene riesgo XSS.
- Integraciones reales requieren credenciales sandbox/reales y runbooks posteriores.

## Rollback

Revertir el commit H2 elimina scripts, job CI, docs y validaciones adicionales. No hay migraciones ni cambios de datos. No se eliminan volumenes.

## Limitaciones aceptadas

- Sin secret manager cloud.
- Sin rotacion real de credenciales.
- Sin MFA/SSO/cookies HttpOnly.
- Sin DAST ni pentest.
- Sin observabilidad distribuida.

## Dependencias hacia H3

H3 debe ampliar observabilidad operacional, correlation IDs, alertas, retencion/retry de webhooks, runbooks operativos y controles distribuidos cuando exista infraestructura real.
