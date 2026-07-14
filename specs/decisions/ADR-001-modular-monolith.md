# ADR-001: Monolito modular

## Estado

Aceptada retrospectivamente.

## Contexto

RealMeet esta en etapa MVP y necesita avanzar con bajo costo operativo, despliegue simple y separacion clara de responsabilidades.

## Decision

Mantener un monolito modular con backend FastAPI y frontend React/Vite, usando modulos por dominio en backend y separacion por paginas, componentes, API, rutas, store y tipos en frontend.

## Evidencia

- Backend: `backend/app/api`, `backend/app/core`, `backend/app/db`, `backend/app/models`, `backend/app/schemas`, `backend/app/services`, `backend/app/repositories`, `backend/app/meetings`, `backend/app/emails`.
- Frontend: `frontend/src/pages`, `frontend/src/components`, `frontend/src/layouts`, `frontend/src/api`, `frontend/src/routes`, `frontend/src/store`, `frontend/src/types`.

## Consecuencias

- Facilita desarrollo inicial y trazabilidad.
- Evita microservicios prematuros.
- Requiere disciplina para no concentrar logica de negocio en routers o componentes.
