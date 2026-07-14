# Reporte de validacion del Modulo 2

## Controles planificados

| ID | Control | Comando / pasos | Resultado esperado | Resultado obtenido | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| M2-VAL-001 | Git baseline | `git status --short --branch`, `git log --oneline -3` | Rama `main`, base `7304f66`, sin cambios versionables | Rama `main`, base confirmada, solo ignorados | aprobado | Ejecutado antes de modificar archivos. |
| M2-VAL-002 | Inspeccion auth backend | `rg` y lectura de auth/security/deps/services/schemas | Riesgos documentados | Riesgos confirmados | aprobado | Fase 2.1. |
| M2-VAL-003 | Inspeccion frontend auth | `rg` y lectura de store/API/rutas/layouts | Riesgos documentados | Riesgos confirmados | aprobado | Fase 2.1. |
| M2-VAL-004 | `git diff --check` fase 2.1 | `git diff --check` | Sin whitespace errors | Sin errores; advertencias CRLF en Windows | aprobado | Fase 2.1 commit `cff0979`. |
| M2-VAL-005 | Tests backend | `docker-compose exec -T backend pytest` | Tests pasan | 17 passed, 1 warning | aprobado | Fase 2.5. |
| M2-VAL-006 | Build frontend | `docker-compose exec -T frontend npm run build` | Build pasa | pendiente | pendiente |  |
| M2-VAL-007 | Health | `GET /health` | 200 | 200 `status=ok` | aprobado | Fase 2.2. |
| M2-VAL-008 | Ready | `GET /ready` | 200 | 200 `status=ready` | aprobado | Fase 2.2. |
| M2-VAL-009 | Login activo | Login demo admin/professional/client | 200/token | pendiente | pendiente |  |
| M2-VAL-010 | Login invalido | Credenciales incorrectas | 401 generico | 401 | aprobado | Runtime Fase 2.2. |
| M2-VAL-011 | Usuario inactivo | Login/acceso con usuario inactivo | 401 | 401 en pruebas unitarias | aprobado | Sin alterar datos demo. |
| M2-VAL-012 | Token invalido/vencido | Requests con token invalido/vencido | 401 | 401 runtime para invalido; vencido cubierto por prueba | aprobado | Fase 2.2. |
| M2-VAL-013 | Rol incorrecto | Cliente a admin/professional; professional a admin | 403 | 403 en helper de rol | aprobado parcial | Prueba unitaria; runtime frontend/backend final pendiente. |
| M2-VAL-014 | Perfil cliente propio | GET/PATCH perfil cliente | Solo datos propios permitidos | Contratos sin campos admin; tests pasan | aprobado parcial | Runtime final pendiente. |
| M2-VAL-015 | Perfil profesional propio | GET/PATCH perfil profesional | Campos base permitidos; futuros bloqueados | Contrato sin campos futuros/admin; tests pasan | aprobado parcial | Runtime final pendiente. |
| M2-VAL-016 | Busqueda de secretos/logs | `rg` de password/token/secret/authorization | Sin exposicion accidental | pendiente | pendiente |  |
| M2-VAL-017 | Npm audit informativo | `npm audit` si entorno lo permite | Severidad documentada | pendiente | pendiente | No ejecutar `npm audit fix --force`. |

## Resultado final

Pendiente. Se completara en Fase 2.7.
