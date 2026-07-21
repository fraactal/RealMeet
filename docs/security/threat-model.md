# RealMeet threat model

Modelo acotado para H2. STRIDE se usa como guia ligera, no como auditoria normativa.

| superficie | activo | amenaza principal | control actual | cambio H2 | riesgo residual | fase futura |
| --- | --- | --- | --- | --- | --- | --- |
| Usuario anonimo | login, catalogo, disponibilidad | fuerza bruta, enumeracion, abuso | rate limit login, errores genericos auth | staging/production exigen rate limit | limite no distribuido | H3/H7 |
| Cliente autenticado | reservas, pagos propios, perfil | acceso cruzado o token robado | dependencias auth, queries por usuario, schemas publicos | docs baseline y pruebas existentes confirmadas | JWT en localStorage | H7 |
| Profesional autenticado | agenda, reservas propias, notas privadas | acceso a reservas ajenas | dependencias professional y filtros por perfil | inventariado en baseline | matriz negativa no exhaustiva | H7 |
| Administrador | integraciones, usuarios, pagos | exposicion de secretos o abuso admin | rutas admin protegidas, referencias de secretos | docs y secret scan/config gate | falta MFA/SSO | H7 |
| Backend | API, logs, secretos en memoria | filtrado de secretos en logs | logging JSON y redaccion por clave | redaccion de patrones en mensajes | no hay SIEM/alertas | H3 |
| Frontend | JWT, UI admin | XSS exfiltra token | rutas protegidas, no secretos VITE | documenta TD-016 y valida env frontend | localStorage | H7 |
| Base de datos | usuarios, reservas, tokens cifrados | fuga o acceso indebido | DB por env, migraciones, hashes/cifrado OAuth | inventario y docs de respuesta | backups/restore no automatizados | H4 |
| WhatsApp webhook | eventos entrantes | spoofing, replay, payload grande | HMAC, verify token, dedupe, limite body | documentado como gate H2 | rate limit/IP proxy pendiente | H3/H5 |
| Mercado Pago webhook | estados de pago | spoofing o aprobacion falsa | firma, dedupe, consulta provider | inventariado y baseline | sandbox real pendiente | H5 |
| Webhooks salientes/n8n | eventos operativos | SSRF, secret leak, replay | HTTPS, URL sin credenciales, HMAC, no redirects | documentado y secret refs | retries/alertas manuales | H3 |
| Google services | OAuth tokens, calendar/docs/sheets | scope excesivo o token expuesto | scopes minimos, tokens cifrados | inventario y baseline | OAuth admin/global | H7 |
| SMTP | credenciales correo | credencial filtrada o email mal enviado | SMTP opcional, log mode por defecto | inventario | sandbox/produccion pendiente | H5 |
| CI | logs, cache, workflow | secret leak, ejecucion privilegiada | no `pull_request_target`, no secrets productivos | `security-check` | SCA backend no bloqueante en H2 | H2/H7 |

## Dependencias hacia fases futuras

- H3: observabilidad, alertas, runbooks y rate limiting distribuido/proxy.
- H4: backups y restore probado.
- H5: E2E e integraciones sandbox reales.
- H7: MFA/SSO, cookies HttpOnly/SameSite, politicas legales y produccion.
