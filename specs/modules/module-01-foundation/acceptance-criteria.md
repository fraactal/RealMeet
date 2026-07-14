# Criterios de aceptacion del Modulo 1

| ID | Criterio | Estado inicial | Estado final | Evidencia |
| --- | --- | --- | --- | --- |
| AC-M1-001 | Variables backend/frontend documentadas en `.env.example`. | parcial | aprobado | `.env.example`, `backend/.env.example`, `frontend/.env.example` |
| AC-M1-002 | Archivos de ejemplo sin secretos reales. | pendiente | aprobado con observaciones | Placeholders locales; `SECRET_KEY=change-me-in-production` documentado solo como ejemplo. |
| AC-M1-003 | `.gitignore` excluye env reales, dependencias, builds, caches y logs sin bloquear `.env.example`. | parcial | aprobado | `.gitignore` |
| AC-M1-004 | Compose puede validarse o se documenta compatibilidad. | parcial | aprobado con observaciones | `docker-compose config` OK; `docker compose` no disponible. |
| AC-M1-005 | PostgreSQL tiene healthcheck y recursos RealMeet. | implementado-no-verificado | aprobado | `docker-compose ps`: `realmeet-db` healthy. |
| AC-M1-006 | Backend espera DB con timeout y error claro. | implementado-no-verificado | aprobado | Logs `waiting_for_database`, `database_ready attempt=1`. |
| AC-M1-007 | Alembic puede correr en base nueva. | no-verificado | aprobado con observaciones | `alembic upgrade head` corre en arranque; DB usada ya tenia volumen existente. |
| AC-M1-008 | Seed es idempotente. | parcial | aprobado | Logs `seed_*_exists` y `seed_completed`; seed ahora verifica por entidad. |
| AC-M1-009 | Backend inicia mediante Docker Compose. | no-verificado | aprobado | `realmeet-backend` healthy. |
| AC-M1-010 | `/health` responde correctamente. | implementado-no-verificado | aprobado | `GET /health` 200. |
| AC-M1-011 | `/ready` responde correctamente y falla controlado. | implementado-no-verificado | aprobado | `GET /ready` 200 con DB y config OK; test cubre fallo controlado. |
| AC-M1-012 | Frontend inicia por Docker Compose. | no-verificado | aprobado | `realmeet-frontend` healthy y HTML responde. |
| AC-M1-013 | Frontend consume backend por configuracion. | implementado-no-verificado | aprobado | `VITE_API_URL`; `/professionals` responde. |
| AC-M1-014 | Login demo funciona si entorno ejecuta. | no-verificado | aprobado | Login admin/client/professional OK. |
| AC-M1-015 | Logs son utiles y no exponen secretos. | parcial | aprobado con observaciones | Logs no muestran passwords/JWT; DB summary oculta password. |
| AC-M1-016 | README tiene pasos reproducibles. | parcial | aprobado | `README.md` actualizado. |
| AC-M1-017 | No se destruyen recursos. | aprobado | aprobado | No se usaron `down -v`, prune ni deletes. |
| AC-M1-018 | Alcance respetado. | aprobado | aprobado | Cambios limitados a fundacion, docs y fixes de build. |
| AC-M1-019 | `REM-P0-001` se valida en runtime si stack opera. | no-verificado | aprobado con observaciones | Cliente/admin con cero reservas no exponen campo; no habia reserva con nota privada para validar contenido. |
| AC-M1-020 | Matriz de trazabilidad actualizada. | pendiente | aprobado | `requirements-matrix.md` |
