# Criterios de aceptacion del Modulo 3

| ID | Criterio | Estado inicial | Estado final | Evidencia |
| --- | --- | --- | --- | --- |
| AC-M3-001 | Usuario publico lista categorias activas. | parcial | pendiente | `GET /categories` existe, pero devuelve activas e inactivas. |
| AC-M3-002 | Usuario publico lista especialidades activas. | parcial | pendiente | `GET /specialties` existe, pero devuelve activas e inactivas. |
| AC-M3-003 | Usuario no admin no crea ni modifica categorias. | implementado-parcial | pendiente | Writes protegidos en `/categories`; falta ruta admin y validacion. |
| AC-M3-004 | Usuario no admin no crea ni modifica especialidades. | implementado-parcial | pendiente | Writes protegidos en `/specialties`; falta ruta admin y validacion. |
| AC-M3-005 | Admin crea y actualiza categorias validas. | parcial | pendiente | Servicio existe sin manejo robusto de duplicados. |
| AC-M3-006 | Admin crea y actualiza especialidades validas. | parcial | pendiente | Servicio existe sin validar categoria activa. |
| AC-M3-007 | No se permiten nombres duplicados segun regla definida. | parcial | pendiente | DB cubre categoria y specialty slug; faltan errores controlados. |
| AC-M3-008 | Categoria/especialidad inactiva no aparece publicamente. | fallido | pendiente | Listados publicos no filtran `is_active`. |
| AC-M3-009 | Profesional consulta especialidades propias. | no-implementado | pendiente |  |
| AC-M3-010 | Profesional actualiza solo especialidades propias. | no-implementado | pendiente |  |
| AC-M3-011 | Profesional no asigna especialidad inexistente o inactiva. | no-implementado | pendiente |  |
| AC-M3-012 | No hay asociaciones duplicadas professional-specialty. | parcial | pendiente | Seed evita duplicados; DB no tiene constraint. |
| AC-M3-013 | Perfil privado no aparece en busqueda publica. | parcial | pendiente | Lista filtra `is_public`; detalle no. |
| AC-M3-014 | Usuario inactivo no aparece publico. | parcial | pendiente | Lista filtra usuario activo; detalle debe revisarse. |
| AC-M3-015 | Perfil publico expone solo campos permitidos. | fallido | pendiente | Usa `UserRead` y expone email/estado/fechas. |
| AC-M3-016 | Perfil publico no expone datos privados. | fallido | pendiente | `UserRead` en `ProfessionalPublicRead`. |
| AC-M3-017 | Profesional edita solo campos publicos autorizados. | parcial | pendiente | M2 permite campos base; faltan categoria/especialidades/is_public en contrato M3. |
| AC-M3-018 | Profesional no edita perfil de otro profesional. | implementado-parcial | pendiente | Endpoints actuales usan usuario autenticado. |
| AC-M3-019 | Busqueda por texto funciona. | parcial | pendiente | Existe sobre nombre y titulo. |
| AC-M3-020 | Filtro por categoria funciona. | parcial | pendiente | Existe sin validacion de categoria activa. |
| AC-M3-021 | Filtro por especialidad funciona. | parcial | pendiente | Existe sin filtrar especialidad activa. |
| AC-M3-022 | Filtros pueden combinarse. | parcial | pendiente | Servicio combina algunos filtros. |
| AC-M3-023 | Paginacion aplica limites validos. | no-implementado | pendiente |  |
| AC-M3-024 | Busqueda sin resultados devuelve vacio coherente. | parcial | pendiente | Sin contrato paginado. |
| AC-M3-025 | Frontend muestra listado, filtros, detalle, loading, error y vacio. | parcial | pendiente | Solo listado/loading/error. |
| AC-M3-026 | Profesional gestiona especialidades y publicacion en frontend. | no-implementado | pendiente |  |
| AC-M3-027 | Admin gestiona categorias/especialidades en UI minima. | no-implementado | pendiente |  |
| AC-M3-028 | `/health` y `/ready` siguen operativos. | verified M2 | pendiente |  |
| AC-M3-029 | Logins demo siguen funcionando. | verified M2 | pendiente |  |
| AC-M3-030 | Pruebas minimas relacionadas pasan. | parcial | pendiente | 17 tests existentes. |
| AC-M3-031 | Frontend compila. | verified M2 | pendiente |  |
| AC-M3-032 | Cada fase completada tiene commit independiente. | pendiente | pendiente |  |
| AC-M3-033 | Matriz de trazabilidad actualizada. | pendiente | pendiente |  |
| AC-M3-034 | No se implementaron disponibilidad, slots ni reservas. | pendiente | pendiente |  |
