# Reporte de validacion del Modulo 3

## Controles planificados

| ID | Control | Comando / pasos | Resultado esperado | Resultado obtenido | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| M3-VAL-001 | Git baseline | `git status --short --branch`, `git log --oneline -8` | Rama `main`, ultimo commit M2, sin cambios versionables | Confirmado | aprobado | Antes de modificar archivos. |
| M3-VAL-002 | Inspeccion backend catalogo | Lectura modelos/schemas/services/routes/migracion/seed | Estado real documentado | Confirmado | aprobado | Fase 3.1. |
| M3-VAL-003 | Inspeccion frontend catalogo | Lectura pagina profesionales, tipos, queries y dashboard | Estado real documentado | Confirmado | aprobado | Fase 3.1. |
| M3-VAL-004 | `git diff --check` | `git diff --check`, `git diff --cached --check` por fase | Sin errores | Sin errores; avisos CRLF Windows | aprobado | Ejecutado antes de commits. |
| M3-VAL-005 | Backend tests | `docker-compose exec -T backend pytest` | Tests pasan | 23 passed, 1 warning | aprobado | Warning conocido de passlib/crypt. |
| M3-VAL-006 | Frontend build | `docker-compose exec -T frontend npm run build` | Build pasa | OK | aprobado | Ejecutado en fases 3.6, 3.7 y cierre. |
| M3-VAL-007 | Docker stack | `docker-compose up --build -d`, `docker-compose ps` | Servicios healthy | backend/db/frontend healthy | aprobado | No se eliminaron volumenes. |
| M3-VAL-008 | Health/ready | `GET /health`, `GET /ready` | 200 | `health=ok`, `ready=ready` | aprobado | Runtime Compose. |
| M3-VAL-009 | Catalogo publico | Categorias/especialidades/profesionales | Solo activos/publicos | OK | aprobado | `/categories` y `/specialties` no exponen `is_active`; `/professionals` paginado. |
| M3-VAL-010 | Admin catalogo | Leer rutas admin con token admin | Admin OK, no admin 403 | `GET /admin/categories` OK con admin | aprobado parcial | No se crearon datos nuevos en runtime para evitar modificar catalogo demo. |
| M3-VAL-011 | Especialidades profesional | GET propias; cliente intenta endpoint profesional | Propias, activas, sin duplicados | Profesional OK; cliente 403 | aprobado | PATCH cubierto por contrato/servicio, no ejecutado para no alterar datos demo. |
| M3-VAL-012 | Perfil publico seguro | Lista/detalle | Sin campos privados | OK | aprobado | JSON publico sin email, phone, estado, timestamps, licencia, verificacion, precio ni direccion. |
| M3-VAL-013 | Filtros/paginacion | search/category/specialty/modality/page | Respuesta paginada coherente | OK | aprobado | Se corrigio bug runtime de `DISTINCT ORDER BY` en PostgreSQL. |
| M3-VAL-014 | Regresion M2 | Login demo y endpoints protegidos | Sin regresiones | admin/professional/client login OK | aprobado | Cliente recibe 403 en endpoint profesional. |
| M3-VAL-015 | Logs | `docker-compose logs --tail=80 backend/frontend/db` | Sin errores graves ni secretos | OK tras fix | aprobado | Logs DB conservan error historico del bug detectado y corregido durante cierre. |
| M3-VAL-016 | Npm audit informativo | `docker-compose exec -T frontend npm audit` | Deuda documentada | 5 vulnerabilities: 1 moderate, 4 high | deuda | No se aplico `audit fix --force` por estar fuera de alcance y cambiar rangos. |

## Resultado final

Modulo 3 queda validado para el alcance solicitado. Se detecto durante runtime un fallo de paginacion en PostgreSQL y se corrigio antes del cierre. Queda deuda de dependencias frontend reportada por `npm audit`.
