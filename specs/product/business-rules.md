# Reglas de negocio

## Reservas

- Un profesional no puede tener dos reservas en el mismo horario.
- Un cliente no debe reservar el mismo bloque dos veces.
- Las reservas usan estados `pending`, `confirmed`, `cancelled`, `completed`, `no_show`.
- Todo cambio de estado debe registrarse en historial.
- No se deben eliminar fisicamente datos sensibles asociados a historial.

Estado Modulo 5: `AppointmentService.create` valida cliente, profesional publico activo, horario futuro, solapamientos activos de profesional y cliente, y pertenencia exacta a un slot disponible calculado por el Modulo 4. La base de datos agrega indices unicos parciales para reservas activas `pending` y `confirmed`. Las transiciones permitidas son `pending -> confirmed`, `pending/confirmed -> cancelled`, `confirmed -> completed` y `confirmed -> no_show`; cada cambio registra historial.

## Disponibilidad

La disponibilidad se calcula usando reglas semanales, duracion de sesion, bloqueos manuales y reservas existentes.

Estado Modulo 4: `AvailabilityService.list_slots` genera slots desde reglas activas, excluye bloqueos `blocked`, reservas `pending`/`confirmed` y slots pasados. Las reglas activas de un mismo profesional no pueden solaparse dentro del mismo dia. La consulta publica queda limitada a 14 dias. Las fechas publicas se interpretan en UTC para el MVP; zonas horarias avanzadas quedan diferidas.

## Privacidad

Las notas privadas del profesional nunca deben ser visibles para el cliente.

Estado Modulo 5: los contratos de salida para cliente y administrador no declaran `professional_private_notes`; el contrato profesional conserva el campo solo para reservas autorizadas. La UI de cliente usa el tipo `Appointment`, que no contiene notas privadas; la UI profesional usa `ProfessionalAppointment`.

## Reuniones y notificaciones

- Las reservas `online` y `hybrid` generan reunion mock.
- Las reservas `presencial` no generan enlace remoto.
- La reunion mock se crea al crear la reserva por coherencia con la implementacion existente.
- Una reserva cancelada conserva datos historicos, pero el contrato marca la reunion como `inactive` y no entrega `join_url`.
- Las notificaciones basicas se registran o envian para creacion, confirmacion y cancelacion.
- Fallos de notificacion no revierten la operacion principal.
- Las notificaciones no incluyen notas privadas ni credenciales.

## Seguridad

- No hardcodear secretos reales.
- Configurar JWT con expiracion.
- Configurar CORS por variables.
- No registrar passwords, tokens ni credenciales.
- Validar permisos por rol.

Estado inicial Modulo 2: login emite JWT con `sub` y `exp`, pero debe rechazar usuarios inactivos; `/users/me` no debe permitir modificar `is_active`; el frontend debe restaurar sesion contra backend y limpiar estado ante `401`.

## Dashboards y administracion

- Las metricas propias se calculan desde el usuario autenticado.
- Las metricas profesionales no aceptan `professional_id` externo.
- Las metricas administrativas son globales y requieren rol admin.
- Las listas administrativas usan paginacion y filtros simples.
- La actualizacion administrativa de profesionales usa una lista cerrada de campos permitidos.
- Desactivar usuarios no elimina reservas ni datos historicos.
- Los endpoints admin no exponen notas privadas profesionales.

Estado Modulo 8: dashboards, metricas y backoffice minimo se consideran parte del MVP funcional para desarrollo local/demo. El cierre valida que las metricas propias deriven del token y que admin use contratos cerrados.

## Perfiles propios

- Un cliente solo puede consultar y actualizar su propio perfil.
- Un profesional solo puede consultar y actualizar su propio perfil.
- Los perfiles propios no pueden modificar `role`, `is_active`, identificadores, hash ni estados administrativos.
- El perfil profesional base del Modulo 2 no incluye categorias, especialidades, precios, publicacion, agenda ni disponibilidad.

## Catalogo profesional

- Las categorias y especialidades inactivas no aparecen en listados publicos.
- Solo administradores pueden crear o modificar categorias y especialidades.
- El profesional solo puede modificar sus propias especialidades.
- Un perfil profesional aparece publicamente solo si el usuario esta activo, es `professional`, el perfil tiene `is_public=true`, categoria activa, titulo y al menos una especialidad activa.
- Los contratos publicos no exponen email, telefono, `is_active`, timestamps, licencias, verificaciones, precios, hashes, tokens, notas ni datos clinicos.
- La busqueda publica debe estar paginada y acotada.

## Cierre MVP

- El MVP se considera cerrado para desarrollo local y demo controlada solo si pasan pruebas backend, build frontend, health/readiness y validaciones acotadas por rol.
- Staging requiere checklist previo, secretos reales, CORS restringido y credenciales demo gestionadas.
- Produccion y uso clinico real quedan fuera de alcance hasta completar hardening, cumplimiento y operacion.

## Hardening tecnico para staging

- Staging y produccion no deben usar secretos placeholder o cortos.
- CORS debe usar origenes explicitos; wildcard no es compatible con credenciales.
- Swagger/OpenAPI debe poder deshabilitarse por configuracion.
- Seed demo no debe ejecutarse automaticamente fuera de entornos locales salvo decision explicita.
- Rate limiting en memoria reduce abuso basico en una sola instancia, pero no reemplaza un control distribuido productivo.
- Backups deben generarse fuera del repositorio y restaurarse primero en entornos aislados.
