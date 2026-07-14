# Modulo 7 - Dashboards, administracion y metricas basicas

## Problema

El MVP tenia reservas y metricas iniciales, pero los dashboards por rol eran parciales y el backoffice administrativo mantenia riesgos de mass assignment, filtros insuficientes y contratos genericos.

## Objetivo

Consolidar dashboards funcionales para cliente, profesional y administrador, y completar un backoffice administrativo minimo con permisos estrictos y contratos seguros.

## Alcance

- Dashboard cliente con resumen de reservas propias.
- Dashboard profesional con metricas propias, estado del perfil y actividad.
- Dashboard admin con metricas globales.
- Filtros y paginacion basica en listas administrativas.
- Gestion administrativa minima de usuarios.
- Gestion administrativa minima de profesionales.
- Consulta administrativa de reservas.
- Correccion de mass assignment en `PATCH /admin/professionals/{id}`.
- Audit log minimo para acciones admin relevantes.
- Frontend de backoffice minimo.

## Exclusiones

- Pagos, facturacion, suscripciones e ingresos reales.
- BI, graficos avanzados o analitica predictiva.
- Exportaciones Excel/PDF.
- Ficha clinica o datos medicos.
- Permisos configurables o roles personalizados.
- Operaciones masivas.
- Eliminacion fisica.

## Actores

- Cliente: consulta metricas y reservas propias.
- Profesional: consulta metricas asociadas a su perfil.
- Admin: consulta metricas globales y gestiona usuarios, profesionales y reservas.

## Metricas

Zona horaria: UTC para metricas diarias del MVP.

- Cliente: proximas reservas, conteos por estado, recientes y proximas.
- Profesional: reservas de hoy, proximas, conteos por estado, clientes unicos, cancelacion, perfil publico y disponibilidad configurada.
- Admin: usuarios, clientes activos, profesionales activos, profesionales publicos, reservas por estado, categorias y especialidades activas, reservas recientes.

## Gestion administrativa

- Usuarios: listar, buscar, filtrar por rol/estado, activar/desactivar y consultar detalle seguro.
- Profesionales: listar, buscar, filtrar por estado/publicacion, consultar detalle, actualizar campos permitidos y activar/desactivar usuario asociado.
- Reservas: listar con filtros basicos, consultar detalle e historial, modificar estado con transiciones validas.

## Seguridad y riesgos

Riesgos identificados:

- Cliente accediendo a metricas globales.
- Profesional accediendo a datos de otro profesional.
- Acceso admin sin rol.
- Mass assignment en profesionales.
- Exposicion de notas privadas en admin.
- Listas sin limites.

Controles implementados:

- Metricas propias derivadas del token.
- `require_admin`, `require_professional` y `require_client`.
- Contratos admin cerrados.
- Paginacion con `page` y `page_size`.
- `AppointmentAdminRead` sin notas privadas.
- Audit log minimo sin payloads sensibles.

Riesgos residuales:

- Audit log no cubre todas las acciones historicas.
- No hay permisos granulares.
- No hay optimizacion profunda para grandes volumenes.

## Validaciones finales

- Backend tests.
- Frontend build.
- `/health` y `/ready`.
- Runtime: dashboards por rol, admin users, profesional update, mass assignment controlado y reservas admin sin notas privadas.
