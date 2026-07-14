# ADR-002: Autenticacion JWT

## Estado

Aceptada retrospectivamente con observaciones.

## Contexto

El MVP requiere autenticacion stateless para API y frontend, con roles `admin`, `professional` y `client`.

## Decision

Usar JWT HS256 con expiracion configurable y password hashing mediante `passlib`.

## Evidencia

- `backend/app/core/security.py` crea y valida tokens con expiracion.
- `backend/app/core/deps.py` obtiene usuario autenticado y valida roles.
- `backend/app/api/routes/auth.py` expone login, registro y `/auth/me`.
- `frontend/src/api/client.ts` adjunta `Authorization: Bearer`.

## Observaciones

El algoritmo y expiracion existen. El secreto se configura por entorno, pero `.env.example` usa `change-me-in-production`, aceptable solo como placeholder local. No se validaron flujos completos por entorno en Modulo 0.
