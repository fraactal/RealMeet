# Post-H2 manual review

Fecha: 2026-07-27
Rama base: `staging`
Commit base: `da1da62`
Rama de trabajo: `codex/post-h2-manual-review`

## Contexto

Esta revision manual cierra la preparacion operativa posterior a H0-H2. No inicia H3, no agrega funcionalidades y no reemplaza la evidencia remota H2, que ya dejo verdes los jobs `security-check`, `backend-tests`, `frontend-build`, `alembic-check`, `openapi-check`, `docker-build` y `smoke-test`.

## Ambiente usado

- Repositorio local: `C:\Users\Jona\Documents\RealMeet`.
- Base: `staging` en `da1da62`.
- Ambiente manual: Docker Compose local.
- Servicios revisados: PostgreSQL, backend FastAPI, frontend Vite y seed local.
- No se registran secretos ni contenido completo de `.env`.

## Flujos revisados

| ID | Area | Accion | Esperado | Resultado | Estado | Fase |
|---|---|---|---|---|---|---|
| MR-001 | Infra local | Levantar Docker Compose | DB, backend y frontend inician | PostgreSQL, migraciones, seed, backend y Vite iniciaron | passed | post-H2 |
| MR-002 | Health | Consultar `/ready` | HTTP 200 | Respondio 200 | passed | post-H2 |
| MR-003 | Auth | Login admin/profesional/cliente | Sesiones validas por rol | Los tres logins funcionaron | passed | post-H2 |
| MR-004 | Admin | Rutas administrativas | Acceso admin autorizado | Rutas respondieron | passed | post-H2 |
| MR-005 | Profesional | Perfil profesional | Lectura/edicion funcional | Perfil funciona | passed | post-H2 |
| MR-006 | Disponibilidad | Configurar disponibilidad | Reglas aplicadas | Disponibilidad funciona | passed | post-H2 |
| MR-007 | Reservas | Crear, confirmar y cancelar | Estados consistentes | Flujo funciono | passed | post-H2 |
| MR-008 | Pagos fake | Checkout/reconcile/retry | Respuestas controladas | Operaciones respondieron | passed | post-H2 |
| MR-009 | Logging | Revisar logs de email | Datos sensibles reducidos | Email parcialmente redactado | observed | H3/H6 |
| MR-010 | Config OAuth | Copiar plantillas locales | Backend inicia sin OAuth | Fallaba por redirect parcial; corregido | fixed | post-H2 |
| MR-011 | Google OAuth | Provider available sin OAuth | 400 controlado | `google_oauth_not_configured`; esperado | accepted | post-H2 |
| MR-012 | Calendario externo | Conflicts con payload invalido | 422 de validacion | Esperado por schema estricto | accepted | post-H2 |
| MR-013 | WhatsApp | Consentimiento con payload invalido | 422 de validacion | Esperado por schema estricto y confirmacion explicita | accepted | post-H2 |
| MR-014 | Pagos | Payment order manual con payload invalido | 422 de validacion | Esperado por schema de monto/campos | accepted | post-H2 |

## Hallazgo OAuth

Las plantillas locales y staging dejaban `GOOGLE_OAUTH_REDIRECT_URI` poblado mientras `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` y `GOOGLE_TOKEN_ENCRYPTION_KEY` estaban vacios. La validacion fail-fast de settings considera que cualquier valor Google OAuth activa la comprobacion de completitud, por lo que el backend rechazaba esa configuracion parcial con:

`Google OAuth settings must be complete when any Google OAuth value is configured`

La regla es correcta y se conserva. La correccion es alinear las plantillas para que OAuth quede completamente deshabilitado por defecto.

## Correccion OAuth

- `.env.example`: `GOOGLE_OAUTH_REDIRECT_URI=` queda vacio; el callback local queda como comentario.
- `backend/.env.example`: mismo comportamiento local.
- `.env.staging.example`: OAuth queda opcional y completamente vacio por defecto; el callback staging sugerido queda como comentario.
- `docker-compose.staging.yml`: el render staging ya no inyecta redirect URI por defecto cuando OAuth esta deshabilitado.
- `backend/tests/test_config.py`: cubre OAuth vacio, redirect parcial rechazado y configuracion completa aceptada.
- `README.md` y `docs/deployment/staging-configuration.md`: documentan que los cuatro valores OAuth deben configurarse juntos o dejarse vacios.

## Respuestas 400/422 evaluadas

- Google provider available con OAuth deshabilitado: 400 esperado. El backend usa `google_oauth_not_configured` cuando faltan valores OAuth.
- Conflictos de calendario con payload invalido: 422 esperado por `CalendarConflictCheckRequest`, que requiere `starts_at` y `ends_at` validos.
- Consentimiento WhatsApp con payload invalido: 422 esperado por schema estricto y `explicit_confirmation=true` obligatorio.
- Creacion manual de payment order con payload invalido: 422 esperado por validadores de Pydantic, incluyendo monto positivo e entero para CLP.

No se identifico bug claro en esos 400/422. Si la UI no muestra mensajes suficientes, queda como pendiente UX para H6, sin redisenar ahora.

## Limitaciones

- No se ejecuto suite completa porque H2 ya tenia CI verde y esta revision solo cambia configuracion/documentacion/pruebas de settings.
- No se probaron credenciales Google reales.
- No se desplego staging real.
- No se hizo auditoria profunda de endpoints, accesibilidad, responsive, performance ni observabilidad.

## Pendientes H3-H7

- H3: observabilidad, correlation IDs, metricas, alertas, runbooks y mejor evidencia operacional.
- H4: backup/restore automatizado y pruebas de recuperacion.
- H5: E2E e integraciones sandbox mas amplias.
- H6: UX de errores para 400/422 y mensajes de validacion en frontend.
- H7: auth productiva avanzada, cookies HttpOnly/SameSite, MFA/SSO y aprobaciones legales/operativas.

## Criterio de cierre

La preparacion post-H2 queda cerrada cuando las plantillas no inducen configuracion OAuth parcial, las pruebas acotadas de settings pasan, Compose renderiza base/staging y el diff queda limpio. `staging` queda preparado para iniciar H3 mediante una rama futura separada.