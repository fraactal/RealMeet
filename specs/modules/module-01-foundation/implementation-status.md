# Estado de implementacion del Modulo 1

Fecha de inicio: 2026-07-14.

## Estado inicial encontrado

- Existe `.env.example` raiz.
- Existen `backend/.env.example` y `frontend/.env.example`.
- `.gitignore` excluye `.env` reales, caches y builds, pero debe verificarse que no bloquee `.env.example`.
- Docker Compose define `db`, `backend`, `frontend`, healthchecks y puertos esperados.
- Backend tiene `app.bootstrap` con espera de DB, Alembic, seed y Uvicorn.
- `wait_for_database` tiene maximo de intentos y error claro con URL sanitizada.
- Alembic lee `DATABASE_URL` desde settings.
- Seed crea datos demo, pero su idempotencia inicial depende de que exista admin demo.
- `/health` y `/ready` existen.
- Frontend usa `VITE_API_URL`.
- README tiene instrucciones, pero mezcla ruta raiz y subproyectos y usa logs `-f` en diagnostico rapido.
- Runtime local de Python/npm no estaba disponible en Modulo 0; debe revalidarse.
- El repositorio completo sigue apareciendo sin tracking en Git.

## Cambios implementados

- `.env.example` raiz ampliado con `APP_NAME`, `APP_ENV`, `API_V1_PREFIX`, `BACKEND_HOST` y `BACKEND_INTERNAL_PORT`.
- `backend/.env.example` y `frontend/.env.example` revisados contra variables consumidas.
- `.gitignore` reorganizado para excluir `.env`, `.env.*`, caches, builds, logs y dependencias, permitiendo `**/.env.example`.
- `docker-compose.yml` alinea variables backend documentadas, mantiene puertos conocidos y usa `npm ci` para frontend.
- `backend/Dockerfile` usa `python -m app.bootstrap` como comando por defecto.
- `frontend/Dockerfile` copia `package-lock.json` y usa `npm ci`.
- `Settings` valida proveedor de reuniones y evita `SECRET_KEY=change-me-in-production` en produccion.
- `/ready` valida configuracion critica y DB.
- `bootstrap` falla temprano si faltan settings criticos.
- Seed refactorizado para ser idempotente por usuario, perfil, categoria, especialidad, relacion profesional-especialidad y disponibilidad.
- Frontend ahora tiene fallback local para `VITE_API_URL`.
- Se agrego `frontend/src/vite-env.d.ts` y se corrigieron tipos minimos de metricas para permitir build.
- README actualizado con Compose v2/v1, envs, logs acotados, reinicio seguro y troubleshooting.

## Estado final

`verified` para ejecucion con Compose v1 (`docker-compose`) en este entorno. Compose v2 sigue no disponible y queda documentado. La validacion de Alembic fue sobre volumen existente, no sobre base nueva. La validacion runtime de `REM-P0-001` fue parcial porque no existian reservas demo con notas privadas.

## Deuda tecnica

- Revisar vulnerabilidades reportadas por `npm ci`: 1 moderada y 4 altas. No se actualizaron dependencias en este modulo para evitar cambios de version fuera de alcance.
- Validar Alembic contra una base completamente nueva en un entorno aislado cuando se permita crear un volumen nuevo.
- Agregar prueba minima de regresion para `REM-P0-001` cuando exista fixture de appointment con nota privada.
- Resolver estado Git: el repositorio completo aparece sin tracking, lo que dificulta trazabilidad de cambios.
- Docker en Windows requiere ejecucion elevada para comandos que consultan daemon.
