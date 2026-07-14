# Estado de implementacion del Modulo 2

Fecha de inicio: 2026-07-14.

## Estado inicial encontrado

- Rama actual: `main`.
- Commit base confirmado: `7304f66 chore: establish RealMeet baseline`.
- Working tree sin cambios versionables al iniciar; solo archivos ignorados de cache/build.
- `POST /auth/login` existe y emite JWT.
- `GET /auth/me` existe y usa `get_current_user`.
- JWT contiene `sub` y `exp`; no se observaron datos sensibles en el token.
- `AuthService.login` valida email/password, pero no valida `is_active`.
- `get_current_user` rechaza usuario inexistente o inactivo, pero no controla `sub` no numerico antes de `int(user_id)`.
- `/users/me` permite actualizar `is_active` por reutilizar `UserUpdate`.
- Router `/admin` esta protegido por `require_roles(UserRole.admin)`.
- Rutas profesionales principales usan `require_roles(UserRole.professional)`.
- No existe perfil propio dedicado para cliente.
- Perfil profesional propio reutiliza `ProfessionalProfileUpdate` con campos fuera de Modulo 2: `category_id`, `specialty_ids`, `price` e `is_public`.
- Frontend almacena token en `localStorage`, protege por presencia de token y no restaura sesion contra `/auth/me`.
- Frontend muestra links por rol, pero las rutas `dashboard/professional` y `dashboard/admin` no tienen guardas de rol.

## Fases

| Fase | Estado | Commit esperado | Observaciones |
| --- | --- | --- | --- |
| 2.1 Baseline y contratos | completada | `cff0979 docs(auth): define module 2 authentication baseline` | Documentacion inicial. |
| 2.2 JWT, usuario activo y errores | completada | `dfa4606 fix(auth): harden jwt validation and authentication errors` | 14 tests backend pasan tras Fase 2.3. |
| 2.3 Autorizacion por rol | completada | `c45aa4e feat(authz): enforce role-based access control` | Helpers de rol aplicados. |
| 2.4 Perfil base de cliente | completada | `f195f93 feat(client): add secure self-service profile` | Contratos y servicio aplicados. |
| 2.5 Perfil base de profesional | completada | `898ebda feat(professional): add secure self-service profile` | Contratos propios restringidos aplicados. |
| 2.6 Sesion y proteccion frontend | en progreso | `feat(frontend-auth): protect sessions and role routes` | Build frontend OK; pendiente commit. |
| 2.7 Validacion integrada y cierre | pendiente | `docs(module-02): close auth and profiles validation` |  |

## Seguridad y riesgos

- Riesgo corregido en Fase 2.2: usuario inactivo ya no puede iniciar sesion.
- Riesgo corregido en Fase 2.2: token con `sub` malformado responde `401` controlado.
- Riesgo reducido en Fase 2.3: permisos por rol ahora tienen helpers explicitos para admin, professional y client.
- Riesgo corregido parcialmente en Fase 2.4: `/users/me` ya no acepta `is_active` y el cliente tiene contrato propio seguro.
- Riesgo corregido en Fase 2.5: perfil profesional propio ya no permite `category_id`, `specialty_ids`, `price`, `is_public`, verificaciones ni licencia.
- Riesgo reducido en Fase 2.6: frontend restaura sesion contra backend, limpia ante `401` y aplica guardas por rol.
- Riesgo aceptado temporalmente: token en `localStorage`.

## Estado final

Pendiente. Este archivo se actualizara al cerrar el modulo.
