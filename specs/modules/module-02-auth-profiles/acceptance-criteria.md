# Criterios de aceptacion del Modulo 2

| ID | Criterio | Estado inicial | Estado final | Evidencia |
| --- | --- | --- | --- | --- |
| AC-M2-001 | Usuario activo con credenciales validas puede iniciar sesion. | implementado | pendiente | Login demo validado en M1; se revalidara en M2. |
| AC-M2-002 | Credenciales incorrectas reciben error controlado sin revelar campo incorrecto. | implementado-parcial | aprobado | Login invalido devuelve `401`; mensaje generico. |
| AC-M2-003 | Usuario inactivo no puede iniciar sesion. | fallido | aprobado | `test_login_rejects_inactive_user`. |
| AC-M2-004 | Usuario inactivo no puede seguir accediendo con token anterior. | implementado-parcial | aprobado | `test_get_current_user_rejects_inactive_user`. |
| AC-M2-005 | Ruta protegida sin token responde `401`. | implementado-parcial | pendiente | `OAuth2PasswordBearer`; falta validacion M2. |
| AC-M2-006 | Token invalido responde `401`. | implementado-parcial | aprobado | `test_decode_token_rejects_invalid_token`; runtime `/auth/me` con token invalido `401`. |
| AC-M2-007 | Token vencido responde `401`. | implementado-parcial | aprobado | `test_decode_token_rejects_expired_token`. |
| AC-M2-008 | `GET /auth/me` devuelve solo datos seguros. | implementado-parcial | pendiente | `UserRead` no expone hash ni password; revisar contrato. |
| AC-M2-009 | Rutas administrativas requieren `admin`. | implementado-parcial | aprobado backend | Helpers `require_admin`; rutas admin/catalogo/metricas admin revisadas. |
| AC-M2-010 | Rutas profesionales requieren `professional` cuando corresponde. | implementado-parcial | aprobado backend | Helpers `require_professional`; rutas perfil, disponibilidad y metricas revisadas. |
| AC-M2-011 | Rutas de cliente requieren `client` cuando corresponde. | implementado-parcial | aprobado parcial | Helper `require_client` en creacion de reservas; perfil cliente se completa en Fase 2.4. |
| AC-M2-012 | Cliente no accede a funciones admin o professional. | implementado-parcial | aprobado backend | `test_role_helpers_reject_wrong_role`; frontend pendiente Fase 2.6. |
| AC-M2-013 | Profesional no modifica perfiles ajenos. | implementado-parcial | pendiente | Perfil propio filtra por `user.id`; falta contrato seguro. |
| AC-M2-014 | Cliente consulta y actualiza unicamente su perfil. | no-implementado | aprobado backend | `GET/PATCH /users/me/profile` con `require_client` y `ProfileService`. |
| AC-M2-015 | Profesional consulta y actualiza unicamente su perfil. | implementado-parcial | pendiente | Existe `/professionals/me/profile`; contrato amplio. |
| AC-M2-016 | Payloads propios no permiten modificar rol, `is_active` ni campos administrativos. | fallido | aprobado parcial | `UserSelfUpdate` y `ClientSelfProfileUpdate` no declaran campos admin; profesional pendiente Fase 2.5. |
| AC-M2-017 | Perfil profesional base no permite modificar categorias, especialidades, precio ni publicacion. | fallido | pendiente | `ProfessionalProfileUpdate` permite esos campos. |
| AC-M2-018 | Logout elimina token y estado local. | implementado | pendiente | Store y navbar lo hacen; se revalidara. |
| AC-M2-019 | Ante `401`, frontend limpia sesion. | no-implementado | pendiente | Falta interceptor de respuesta. |
| AC-M2-020 | Frontend restringe rutas segun rol. | parcial | pendiente | Links por rol existen; rutas no. |
| AC-M2-021 | Seguridad continua aplicada en backend. | parcial | pendiente | Backend debe seguir siendo autoridad. |
| AC-M2-022 | No se exponen hashes, secretos ni informacion interna. | parcial | pendiente | Revisar schemas, logs y busquedas estaticas. |
| AC-M2-023 | Backend, frontend y PostgreSQL continuan funcionando. | verificado M1 | pendiente | Validacion integrada M2. |
| AC-M2-024 | `/health` y `/ready` continuan operativos. | verificado M1 | aprobado parcial | Runtime `GET /health` y `GET /ready` OK tras Fase 2.2. |
| AC-M2-025 | Frontend compila. | verificado M1 | pendiente | Build M2. |
| AC-M2-026 | Pruebas minimas relacionadas pasan. | parcial | aprobado parcial | `docker-compose exec -T backend pytest`: 16 passed. |
| AC-M2-027 | Cada fase tiene commit independiente. | pendiente | pendiente | Git. |
| AC-M2-028 | Matriz de trazabilidad actualizada. | pendiente | pendiente | `requirements-matrix.md`. |
| AC-M2-029 | No se implementaron funciones del Modulo 3. | pendiente | pendiente | Revision de cambios. |
