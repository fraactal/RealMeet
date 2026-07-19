# Spec - Plan de preparacion productiva

## Objetivo

Consolidar deuda tecnica y riesgos del MVP funcional de RealMeet en un plan accionable para avanzar desde `staging` integrado hacia staging desplegable, piloto controlado y produccion.

## Alcance

- Revisar reviews y closeout del MVP.
- Revisar README, `.env.example`, Docker Compose, configuracion backend/frontend, logging, seguridad, tests, dependencias y documentacion operativa disponible.
- Crear registros de deuda, gates por ambiente, roadmap de hardening y riesgos.
- Documentar propuesta futura de CI/CD y testing.

## Fuera de alcance

- Correcciones funcionales.
- Tests nuevos.
- Actualizacion de dependencias.
- Workflows CI/CD.
- Cambios de Dockerfiles o configuracion runtime.
- Deploy, merge a `main`, tag o inicio de fase H0.

## Fuentes revisadas

- `docs/reviews/pre-mvp-integration-review.md`
- `docs/reviews/mvp-final-integration-review.md`
- `docs/mvp/mvp-functional-closeout.md`
- `specs/reviews/pre-mvp-integration-review/spec.md`
- `specs/reviews/mvp-final-integration-review/spec.md`
- `README.md`
- `.env.example`
- `backend/.env.example`
- `frontend/.env.example`
- `docker-compose.yml`
- `backend/app/core/config.py`
- `backend/app/core/logging.py`
- `backend/app/core/middleware.py`
- `backend/app/core/security.py`
- `backend/app/core/runtime.py`
- `backend/app/main.py`
- `backend/app/bootstrap.py`
- `backend/alembic.ini`
- `backend/requirements.txt`
- `backend/pytest.ini`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `specs/modules/module-08-mvp-closure/staging-checklist.md`
- `specs/modules/module-08-mvp-closure/validation-report.md`

## Documentos generados

- `docs/hardening/technical-debt-register.md`
- `docs/hardening/environment-readiness-gates.md`
- `docs/hardening/production-readiness-roadmap.md`
- `docs/hardening/mvp-risk-register.md`
- `specs/hardening/production-readiness-plan/spec.md`

## Criterios de aceptacion

- Registro tecnico consolidado sin duplicar hallazgos.
- Cada hallazgo incluye ID, categoria, titulo, descripcion, evidencia, impacto, probabilidad, severidad, esfuerzo, dependencias, bloqueos, recomendacion y estado.
- Priorizacion P0/P1/P2/P3 balanceada.
- Gates objetivos para desarrollo local, staging, piloto y produccion.
- Roadmap H0-H7 con objetivo, alcance, fuera de alcance, dependencias, criterios, riesgos, validaciones y commit esperado.
- Registro de riesgos con mitigacion, contingencia, owner y fase objetivo.
- README referencia la fase de hardening sin introducir cambios funcionales.
- `git diff --check` pasa.
- Un unico commit documental: `docs(hardening): define production readiness roadmap`.

## Validacion minima

Ejecutar solo:

```bash
git diff --check
```

No ejecutar suite completa, build, servicios, deploy ni correcciones.
