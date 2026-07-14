# Reporte de validacion del Modulo 1

## Controles planificados

| ID | Control | Comando / pasos | Resultado esperado | Resultado obtenido | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| M1-VAL-001 | Inventario variables | `rg` sobre backend, frontend, Compose y env examples | Variables consumidas documentadas | Variables backend/frontend/Compose alineadas en env examples | aprobado |  |
| M1-VAL-002 | Git status | `git status --short` | Identificar cambios y riesgo tracking | Todo el repo aparece sin tracking | aprobado con observaciones | Riesgo preexistente. |
| M1-VAL-003 | Compose v2 config | `docker compose config` | Config valida o limitacion clara | Falla: Docker sin subcomando `compose` | fallido | Usar `docker-compose` en este host. |
| M1-VAL-004 | Compose v1 config | `docker-compose config` | Config valida si v1 disponible | Config valida con advertencia de acceso a config Docker | aprobado con observaciones | Requiere elevacion para daemon. |
| M1-VAL-005 | Backend tests existentes | `docker-compose exec -T backend pytest` | Tests health/config pasan | 6 passed, 1 warning | aprobado | Ejecutado dentro del contenedor. |
| M1-VAL-006 | Frontend build | `docker-compose exec -T frontend npm run build` | Build pasa | Build exitoso tras correccion minima de tipos | aprobado | `dist/` generado e ignorado. |
| M1-VAL-007 | Docker up | `docker-compose up --build -d` | Stack inicia | db/backend/frontend healthy | aprobado | Requirio ejecucion elevada. |
| M1-VAL-008 | Health | `curl http://localhost:18000/health` | 200 JSON estable | 200 `{"status":"ok","environment":"docker"}` | aprobado |  |
| M1-VAL-009 | Ready | `curl http://localhost:18000/ready` | 200 con DB disponible | 200 `{"status":"ready","database":"ok","configuration":"ok"}` | aprobado |  |
| M1-VAL-010 | Login demo | `POST /api/v1/auth/login` | Token para usuario demo | Login OK para admin, client y professional | aprobado | Tokens no se documentan. |
| M1-VAL-011 | REM-P0-001 runtime | Reservas cliente/admin no incluyen notas privadas | Campo ausente | Campo ausente en respuestas vacias de cliente/admin | aprobado con observaciones | No habia reservas con nota privada para validar payload con contenido. |
| M1-VAL-012 | Frontend HTTP | `curl http://localhost:15173` | HTML de Vite responde | 200 OK | aprobado |  |
| M1-VAL-013 | Profesionales publico | `GET /api/v1/professionals` | 200 con profesional demo | 200 OK con profesional demo | aprobado |  |
| M1-VAL-014 | Env reales | `Test-Path .env`, `backend/.env`, `frontend/.env` | No existen env reales versionables | No existen | aprobado |  |
| M1-VAL-015 | Secretos evidentes | `rg` de `SECRET_KEY`, passwords, tokens y Authorization | Solo placeholders o referencias de codigo | Sin secretos reales detectados | aprobado con observaciones | `.env.example` usa credenciales demo/locales. |
| M1-VAL-016 | Ignorados generados | `git check-ignore frontend/dist/index.html frontend/node_modules/.package-lock.json` | Archivos generados ignorados | Ignorados por `.gitignore` | aprobado |  |

## Resultado final

Modulo 1 validado en runtime con Docker Compose v1. Compose v2 no esta disponible en el host inspeccionado. Backend, frontend y DB quedan operativos y healthy. No se ejecutaron comandos destructivos.
