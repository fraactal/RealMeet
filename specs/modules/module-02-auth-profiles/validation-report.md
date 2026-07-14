# Reporte de validacion del Modulo 2

## Controles planificados

| ID | Control | Comando / pasos | Resultado esperado | Resultado obtenido | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| M2-VAL-001 | Git baseline | `git status --short --branch`, `git log --oneline -3` | Rama `main`, base `7304f66`, sin cambios versionables | Rama `main`, base confirmada, solo ignorados | aprobado | Ejecutado antes de modificar archivos. |
| M2-VAL-002 | Inspeccion auth backend | `rg` y lectura de auth/security/deps/services/schemas | Riesgos documentados | Riesgos confirmados | aprobado | Fase 2.1. |
| M2-VAL-003 | Inspeccion frontend auth | `rg` y lectura de store/API/rutas/layouts | Riesgos documentados | Riesgos confirmados | aprobado | Fase 2.1. |
| M2-VAL-004 | `git diff --check` fase 2.1 | `git diff --check` | Sin whitespace errors | Sin errores; advertencias CRLF en Windows | aprobado | Fase 2.1 commit `cff0979`. |
| M2-VAL-005 | Tests backend | `docker-compose exec -T backend pytest` | Tests pasan | 17 passed, 1 warning | aprobado | Fase 2.7. |
| M2-VAL-006 | Build frontend | `docker-compose exec -T frontend npm run build` | Build pasa | Build exitoso | aprobado | Fase 2.6. |
| M2-VAL-007 | Health | `GET /health` | 200 | 200 `status=ok` | aprobado | Fase 2.2. |
| M2-VAL-008 | Ready | `GET /ready` | 200 | 200 `status=ready` | aprobado | Fase 2.2. |
| M2-VAL-009 | Login activo | Login demo admin/professional/client | 200/token | OK para los tres roles | aprobado | Tokens no impresos. |
| M2-VAL-010 | Login invalido | Credenciales incorrectas | 401 generico | 401 | aprobado | Runtime Fase 2.2. |
| M2-VAL-011 | Usuario inactivo | Login/acceso con usuario inactivo | 401 | 401 en pruebas unitarias | aprobado | Sin alterar datos demo. |
| M2-VAL-012 | Token invalido/vencido | Requests con token invalido/vencido | 401 | 401 runtime para invalido; vencido cubierto por prueba | aprobado | Fase 2.2. |
| M2-VAL-013 | Rol incorrecto | Cliente a admin/professional; professional a admin | 403 | Cliente contra admin/professional metrics responde 403 | aprobado |  |
| M2-VAL-014 | Perfil cliente propio | GET/PATCH perfil cliente | Solo datos propios permitidos | Runtime responde `birth_date,notes,user` | aprobado | Payload con `is_active`/`role` ignorado por contrato. |
| M2-VAL-015 | Perfil profesional propio | GET/PATCH perfil profesional | Campos base permitidos; futuros bloqueados | Runtime sin campos futuros/admin | aprobado | Payload con `price`, `is_public`, `category_id`, `specialty_ids` no aparece en respuesta. |
| M2-VAL-016 | Busqueda de secretos/logs | Revision de schemas/logs y logs backend | Sin exposicion accidental | Sin tokens/passwords en logs; `/auth/me` sin password/hash | aprobado |  |
| M2-VAL-017 | Npm audit informativo | `docker-compose exec -T frontend npm audit` | Severidad documentada | 5 vulnerabilidades: 1 moderate, 4 high | aprobado con deuda | No se ejecuto `npm audit fix --force`. |

## Resultado final

Modulo 2 validado con Docker Compose v1. Backend, frontend y PostgreSQL quedaron healthy. No se detectaron errores de serializacion en logs backend. Las vulnerabilidades npm quedan como deuda separada porque las correcciones sugeridas requieren `npm audit fix --force` y cambios fuera de rango.
