# Criterios de aceptacion del Modulo 2

| ID | Criterio | Estado inicial | Estado final | Evidencia |
| --- | --- | --- | --- | --- |
| AC-M2-001 | Usuario activo con credenciales validas puede iniciar sesion. | implementado | aprobado | Login admin/client/professional OK en runtime M2. |
| AC-M2-002 | Credenciales incorrectas reciben error controlado sin revelar campo incorrecto. | implementado-parcial | aprobado | Login invalido devuelve `401`; mensaje generico. |
| AC-M2-003 | Usuario inactivo no puede iniciar sesion. | fallido | aprobado | `test_login_rejects_inactive_user`. |
| AC-M2-004 | Usuario inactivo no puede seguir accediendo con token anterior. | implementado-parcial | aprobado | `test_get_current_user_rejects_inactive_user`. |
| AC-M2-005 | Ruta protegida sin token responde `401`. | implementado-parcial | aprobado | `/auth/me` sin token responde `401`. |
| AC-M2-006 | Token invalido responde `401`. | implementado-parcial | aprobado | `test_decode_token_rejects_invalid_token`; runtime `/auth/me` con token invalido `401`. |
| AC-M2-007 | Token vencido responde `401`. | implementado-parcial | aprobado | `test_decode_token_rejects_expired_token`. |
| AC-M2-008 | `GET /auth/me` devuelve solo datos seguros. | implementado-parcial | aprobado | Campos: `id,email,first_name,last_name,phone,role,is_active,created_at,updated_at`; sin password/hash/token. |
| AC-M2-009 | Rutas administrativas requieren `admin`. | implementado-parcial | aprobado backend | Helpers `require_admin`; rutas admin/catalogo/metricas admin revisadas. |
| AC-M2-010 | Rutas profesionales requieren `professional` cuando corresponde. | implementado-parcial | aprobado backend | Helpers `require_professional`; rutas perfil, disponibilidad y metricas revisadas. |
| AC-M2-011 | Rutas de cliente requieren `client` cuando corresponde. | implementado-parcial | aprobado parcial | Helper `require_client` en creacion de reservas; perfil cliente se completa en Fase 2.4. |
| AC-M2-012 | Cliente no accede a funciones admin o professional. | implementado-parcial | aprobado backend | `test_role_helpers_reject_wrong_role`; frontend pendiente Fase 2.6. |
| AC-M2-013 | Profesional no modifica perfiles ajenos. | implementado-parcial | aprobado backend | `ProfessionalService` usa `user.id` autenticado para perfil propio. |
| AC-M2-014 | Cliente consulta y actualiza unicamente su perfil. | no-implementado | aprobado backend | `GET/PATCH /users/me/profile` con `require_client` y `ProfileService`. |
| AC-M2-015 | Profesional consulta y actualiza unicamente su perfil. | implementado-parcial | aprobado backend | `ProfessionalSelfProfileRead/Update` en endpoints propios. |
| AC-M2-016 | Payloads propios no permiten modificar rol, `is_active` ni campos administrativos. | fallido | aprobado backend | Contratos self-service de usuario, cliente y profesional no declaran campos admin. |
| AC-M2-017 | Perfil profesional base no permite modificar categorias, especialidades, precio ni publicacion. | fallido | aprobado backend | `ProfessionalSelfProfileUpdate` excluye esos campos; test de contrato agregado. |
| AC-M2-018 | Logout elimina token y estado local. | implementado | aprobado frontend | Store limpia token/user/restoring y Navbar redirige a login. |
| AC-M2-019 | Ante `401`, frontend limpia sesion. | no-implementado | aprobado frontend | Interceptor Axios ejecuta `logout()` ante `401`. |
| AC-M2-020 | Frontend restringe rutas segun rol. | parcial | aprobado frontend | `RequireAuth` acepta `allowedRoles` y protege metricas admin/professional. |
| AC-M2-021 | Seguridad continua aplicada en backend. | parcial | aprobado | Roles y perfiles protegidos en backend; frontend solo complementa. |
| AC-M2-022 | No se exponen hashes, secretos ni informacion interna. | parcial | aprobado | Schemas y logs revisados; no se imprimieron tokens en validacion. |
| AC-M2-023 | Backend, frontend y PostgreSQL continuan funcionando. | verificado M1 | aprobado | `docker-compose ps`: db/backend/frontend healthy. |
| AC-M2-024 | `/health` y `/ready` continuan operativos. | verificado M1 | aprobado | Runtime `GET /health` y `GET /ready` OK. |
| AC-M2-025 | Frontend compila. | verificado M1 | aprobado | `docker-compose exec -T frontend npm run build` OK. |
| AC-M2-026 | Pruebas minimas relacionadas pasan. | parcial | aprobado parcial | `docker-compose exec -T backend pytest`: 17 passed. |
| AC-M2-027 | Cada fase tiene commit independiente. | pendiente | aprobado | Commits `cff0979`, `dfa4606`, `c45aa4e`, `f195f93`, `898ebda`, `c2058ed` y cierre documental. |
| AC-M2-028 | Matriz de trazabilidad actualizada. | pendiente | aprobado | `requirements-matrix.md`. |
| AC-M2-029 | No se implementaron funciones del Modulo 3. | pendiente | aprobado | Sin categorias/especialidades/disponibilidad/reservas nuevas. |
