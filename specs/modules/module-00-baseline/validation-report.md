# Reporte de validacion del Modulo 0

## Controles ejecutados

| ID | Control | Comando / pasos | Esperado | Obtenido | Estado | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| VAL-001 | Inventario de archivos | `rg --files` | Listado completo del repo | Se listaron backend, frontend, Docker, README, tests y migracion | aprobado | No existian `specs/` antes de este modulo. |
| VAL-002 | Estado git | `git status --short` | Identificar cambios previos | Todo el repo aparece sin trackear | aprobado con observaciones | Se evitaron cambios fuera de `specs/`. |
| VAL-003 | Docker Compose config moderno | `docker compose config` | Config valida | Falla: Docker sin subcomando `compose`; advertencia de acceso a config | fallido | Entorno local no tiene plugin Compose v2 disponible. |
| VAL-004 | Docker Compose config clasico | `docker-compose config` | Config valida | Genera configuracion de servicios, puertos y healthchecks | aprobado con observaciones | Docker advierte `Acceso denegado` al leer `C:\Users\Jona\.docker\config.json`. |
| VAL-005 | Docker Compose estado | `docker compose ps` | Estado de servicios | Falla por ausencia de subcomando `compose` | fallido | No se intento detener ni levantar servicios. |
| VAL-006 | Pytest backend | `pytest` en `backend` | Ejecutar tests existentes | `pytest` no esta en PATH | blocked | No se instalaron dependencias por alcance. |
| VAL-007 | Version Python local | `python --version` | Version disponible | Acceso denegado a `python.exe` | blocked | No se uso runtime alternativo. |
| VAL-008 | Version npm local | `npm --version` | Version disponible | `npm` no esta en PATH | blocked | No se pudo ejecutar build frontend. |
| VAL-009 | Build frontend | `npm run build` | Build exitoso | `npm` no esta en PATH | blocked | Validacion limitada a inspeccion estatica. |
| VAL-010 | Inspeccion de rutas backend | Lectura de `backend/app/api/routes/*.py` | Endpoints y permisos identificados | Rutas por dominio identificadas | aprobado | Ver matriz. |
| VAL-011 | Inspeccion migracion | Lectura de `backend/alembic/versions/20260611_0001_initial.py` | Tablas principales presentes | Tablas y enums principales presentes | aprobado con observaciones | No ejecutada contra DB. |
| VAL-012 | Inspeccion seed | Lectura de `backend/app/seed/run.py` | Datos demo requeridos presentes | Usuarios demo, categorias, especialidades y disponibilidad presentes | aprobado con observaciones | No ejecutado contra DB. |
| VAL-013 | Inspeccion privacidad notas | Lectura de schemas y appointments | Notas privadas no expuestas a clientes | `AppointmentRead` incluye `professional_private_notes` | fallido | Hallazgo P0/P1 para Modulo 5 o correccion previa. |
| VAL-014 | Remediacion privacidad notas | `rg -n "AppointmentRead\|professional_private_notes"` y revision de schemas/rutas | Cliente/admin sin contrato con notas privadas; profesional autorizado conserva acceso | `AppointmentRead` ya no se usa; existen `AppointmentClientRead`, `AppointmentProfessionalRead`, `AppointmentAdminRead`; el payload generico `AppointmentStatusUpdate` no declara notas privadas | aprobado por inspeccion estatica | Runtime no ejecutado por limitaciones de Python/Docker registradas en VAL-003 a VAL-009. |
| VAL-015 | Intento de validacion runtime Python | `python --version` fuera del sandbox | Python disponible para importar backend o correr pytest | Python no esta instalado o no esta disponible en PATH | blocked | No se ejecutaron pruebas por entorno; no se instalaron dependencias por alcance. |

## Validaciones no realizadas

- `docker compose up --build`: no ejecutado para evitar accion larga y porque Compose v2 no esta disponible; Compose clasico solo se uso para config.
- Llamadas `/health`, `/ready`, login y endpoints: no realizadas porque no se levanto backend.
- Navegacion frontend: no realizada porque no se levanto frontend.
- `alembic upgrade head`: no ejecutado por falta de Python operativo local y DB levantada.
- Seed real: no ejecutado por falta de DB y runtime.

## Resultado general

La inspeccion estatica permite crear baseline SDD. La validacion ejecutable queda incompleta por limitaciones del entorno local, por lo que varias capacidades deben permanecer en `implemented-unverified` o `partial`.
