# H2 seguridad y secretos

## Alcance

H2 endurece configuracion sensible, redaccion de logs, CI de seguridad, inventario de secretos y documentacion de amenazas. No despliega, no rota credenciales reales, no agrega funcionalidades y no inicia H3.

## Hallazgos atendidos

| hallazgo | estado anterior | cambio H2 | evidencia | estado final |
| --- | --- | --- | --- | --- |
| TD-002 | mitigated-h0 | H2 agrega inventario, escaneo de secretos y gate de configuracion sensible | `docs/security/secrets-inventory.md`, `scripts/ci/secret_scan.py`, `scripts/ci/check_security_config.py` | mitigated, pending remote evidence |
| TD-012 | planned | Runbook/inventario por categoria de integracion y politica de referencias | `docs/security/secrets-inventory.md` | mitigated, pending remote evidence |
| TD-013 | documented | Threat model y baseline consolidan firma, dedupe, timeouts y limitaciones de webhooks | `docs/security/threat-model.md`, `docs/security/security-baseline.md` | mitigated |
| TD-016 | documented | Riesgo `localStorage` documentado sin rediseñar auth | `docs/security/security-baseline.md` | accepted |
| TD-017 | documented | Staging/production rechazan `RATE_LIMIT_ENABLED=false`; limitacion multi-instancia documentada | `backend/app/core/config.py`, `backend/tests/test_config.py` | mitigated |
| TD-018 | planned | Se confirma matriz critica existente y se agregan pruebas de settings/logging; auditoria exhaustiva queda futura | `backend/tests/test_config.py`, `backend/tests/test_security_hardening.py` | mitigated |
| TD-019 | documented | CI agrega `security-check` con secretos/config y `npm audit --audit-level=critical` | `.github/workflows/ci.yml` | mitigated, pending remote evidence |
| TD-026 | documented | Warning `passlib/crypt` evaluado como no bloqueante en Python 3.12 | suite backend H2 | accepted |

## Cambios

- `security-check` en CI.
- Escaneo de secretos sin imprimir valores.
- Validacion de workflow/env templates sensibles.
- Redaccion de tokens, firmas y passwords en mensajes de log.
- Rango seguro para expiracion JWT.
- Rate limit obligatorio en staging/production.
- Documentos H2 de baseline, inventario y amenazas.

## Evidencia

H1 remoto verde base: https://github.com/fraactal/RealMeet/actions/runs/29785958214.

La evidencia remota H2 queda pendiente hasta el push de `codex/h2-security-secrets`.

## Pruebas

Validaciones H2 esperadas:

- `pytest tests/test_config.py tests/test_security_hardening.py -vv`.
- `pytest`.
- `python scripts/ci/secret_scan.py`.
- `python scripts/ci/check_security_config.py`.
- `npm audit --audit-level=critical`.
- `git diff --check`.

## Gates CI

`security-check` falla si:

- aparecen patrones de secretos de alta confianza;
- workflow usa `pull_request_target`, `secrets.*` o pierde `contents: read`;
- staging template habilita defaults inseguros;
- frontend expone variables distintas de `VITE_API_URL`;
- `npm audit` encuentra vulnerabilidades criticas.

## Vulnerabilidades encontradas

- No se encontraron secretos reales en el arbol versionado actual mediante el escaneo H2.
- Las vulnerabilidades frontend high conocidas siguen documentadas; H2 no ejecuta `npm audit fix` ni upgrades masivos.

## Vulnerabilidades aceptadas

- `localStorage` para JWT: aceptada hasta rediseño auth/cookies.
- Rate limiter en memoria: aceptado para staging/piloto acotado, no para multi-instancia.
- `passlib/crypt` warning: aceptado para Python 3.12, revisar antes de Python 3.13.

## Limitaciones

- Escaneo de secretos no reemplaza GitHub secret scanning ni revision manual.
- No hay secret manager real ni rotacion automatica.
- No hay SAST profundo ni DAST.
- No hay rate limiting distribuido.
- Integraciones reales siguen pendientes de sandbox/operacion.

## Riesgos residuales

- XSS podria exfiltrar JWT.
- Credenciales reales dependen de provision externa correcta.
- Webhooks requieren proxy/IP/rate limiting operativo futuro.
- Vulnerabilidades high frontend requieren politica de upgrade controlado.

## Elementos diferidos

- Escaneo historico Git completo: deferred; puede generar falsos positivos, no debe bloquear H2 y cualquier exposicion historica requiere rotacion y analisis especifico sin reescribir historial automaticamente.
- Secret manager real: deferred hasta definir plataforma de hosting.
- Rotacion real de credenciales: deferred; requiere owners y proveedores externos.
- Rate limit distribuido: deferred; requiere gateway, Redis o WAF.
- Migracion desde `localStorage`: deferred; requiere redisenar auth hacia cookies HttpOnly/SameSite y CSRF.
- Pentesting y auditoria profunda de auth/webhooks: deferred a seguridad profunda.
- `passlib`/Python 3.13: deferred hasta plan de upgrade de runtime.
- H3: observabilidad, alertas, runbooks, retry/retencion operacional.
- H4: backups/restore.
- H5: E2E e integraciones sandbox.
- H7: auth productiva avanzada, MFA/SSO/cookies y aprobacion legal/operativa.

## Relacion con H3

H3 debe construir sobre los controles H2 para agregar evidencia operacional: correlation IDs, metricas, alertas accionables y procedimientos de incidente sin filtrar datos sensibles.
