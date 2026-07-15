# Submodulo 10.5 - Experiencia administrativa

## Objetivo

Redisenar la experiencia administrativa existente para que el admin pueda revisar el estado operativo de RealMeet, gestionar usuarios, profesionales, reservas, categorias y especialidades con una interfaz clara y consistente.

## Alcance

- Dashboard administrativo en `/dashboard`.
- Metricas administrativas en `/dashboard/admin`.
- Backoffice combinado en `/dashboard/admin/manage`.
- Catalogo administrativo en `/dashboard/admin/catalog`.
- Componentes reutilizables bajo `frontend/src/components/admin/`.
- Estados de carga, error y vacio con componentes globales.

## Fuera de alcance

- Cambios backend, APIs, migraciones o permisos.
- Nuevas metricas, nuevos filtros, acciones masivas, exportaciones o eliminacion permanente.
- Auditoria frontend, porque no existe una ruta funcional actual.
- Redisenos cliente, profesional, landing o shell global.

## Rutas afectadas

- `/dashboard`
- `/dashboard/admin`
- `/dashboard/admin/manage`
- `/dashboard/admin/catalog`

## Datos reales utilizados

- `/admin/metrics`: totales de usuarios, clientes, profesionales, reservas por estado, categorias, especialidades y reservas recientes.
- `/admin/users`: usuarios paginados con busqueda, rol y estado.
- `/admin/professionals`: profesionales paginados con busqueda, estado de usuario y estado publico.
- `/admin/appointments`: reservas paginadas con busqueda y estado.
- `/admin/categories`: categorias, estado y creacion/actualizacion.
- `/admin/specialties`: especialidades, categoria asociada, estado y creacion/actualizacion.

## Componentes previstos

- `AdminMetricCard`
- `AdminQuickActions`
- `AdminAppointmentCard`
- `AdminPagination`
- `AdminStatusPill`

## Riesgos

- El contrato de reservas administrativas no entrega nombres de cliente/profesional, por lo que se usa una presentacion neutral.
- La pantalla de backoffice agrupa usuarios, profesionales y reservas porque el router actual no separa esas secciones.
- No existe vista frontend de auditoria.

## Validacion minima

- `docker-compose exec -T frontend npm run build`
- Revision manual de dashboard admin, metricas, usuarios, profesionales, reservas, catalogo, filtros, paginacion y responsive aproximado.
