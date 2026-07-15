# Reporte de validacion del Modulo 9

## Controles estaticos

| Control | Resultado | Evidencia |
| --- | --- | --- |
| Git inicial | aprobado | `main`, ultimo commit `695e6c7`. |
| Riesgos M8 revisados | aprobado | Settings, main, bootstrap, Dockerfiles, envs, logs y docs. |
| Dependencias nuevas | aprobado | No se agregan dependencias. |
| Migraciones | aprobado | No hay cambios de esquema. |
| Funcionalidad comercial/clinica nueva | aprobado | No se implementa. |

## Validacion final

| Control | Resultado | Evidencia |
| --- | --- | --- |
| `docker-compose up --build -d` | aprobado | DB/backend/frontend healthy. |
| `docker-compose exec -T backend pytest` | aprobado | `52 passed, 1 warning in 3.63s`. |
| `docker-compose exec -T frontend npm run build` | aprobado con observacion | Primeros intentos detectaron carrera `npm ci` y permisos de `dist`; corregido con volumenes nombrados. Build final OK. |
| `docker-compose exec -T frontend npm audit` | aprobado informativo | 5 vulnerabilidades: 1 moderate, 4 high. |
| `/health` | aprobado | HTTP 200. |
| `/ready` | aprobado | HTTP 200. |
| Headers | aprobado | `nosniff`, `DENY`, `strict-origin-when-cross-origin`, Permissions-Policy. |
| CORS permitido | aprobado | `Access-Control-Allow-Origin: http://localhost:15173`. |
| CORS no permitido | aprobado | Sin `Access-Control-Allow-Origin`. |
| Rate limit login | aprobado | 10 respuestas `401`; luego `429,429`. |
| Swagger dev | aprobado | `/api/v1/docs` y `/api/v1/openapi.json` HTTP 200. |
| Logs backend | aprobado | Sin tokens, passwords, secrets ni Authorization; se ve `429` esperado. |
| Logs frontend | aprobado con observacion | Vite listo; audit informa vulnerabilidades conocidas. |

## Dependencias vulnerables

- `axios`: high, runtime frontend/API client; fix reportado por npm via `--force` hacia `axios@1.18.1`.
- `react-router` / `react-router-dom`: high, runtime routing; fix reportado via `--force` hacia `react-router-dom@7.18.1`.
- `vite`: high, dev/build tooling; fix reportado via `--force` hacia `vite@7.3.6`.
- `postcss`: moderate, build/CSS tooling; fix reportado via `--force` hacia `postcss@8.5.19`.

No se actualizan dependencias en M9 porque npm propone `npm audit fix --force` y cambios fuera del rango declarado.

## Resultado final

Modulo 9 validado para hardening tecnico de staging. Staging queda mejor preparado, pero produccion y uso clinico real siguen fuera de alcance.
