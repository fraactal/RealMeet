# Diseno tecnico del Modulo 7

## Backend

- `ClientDashboard` se expone en `GET /client/metrics`.
- `ProfessionalMetrics` se amplia sin recibir `professional_id` desde frontend.
- `AdminMetrics` se amplia para conteos globales por estado y catalogo.
- `AdminUser*`, `AdminProfessional*` y `AdminAppointmentListResponse` definen contratos administrativos.
- `PATCH /admin/professionals/{id}` usa `AdminProfessionalUpdate` con lista cerrada de campos permitidos.
- `AuditLog` se usa para actualizacion admin de usuarios, profesionales y reservas.

## Paginacion y filtros

Listas admin aceptan:

- `page >= 1`
- `page_size <= 100`
- `search`
- filtros simples por rol, estado, publicacion o status segun recurso.

## Frontend

- `DashboardHomePage` muestra dashboard propio para clientes.
- `ProfessionalMetricsPage` muestra resumen profesional ampliado.
- `AdminMetricsPage` muestra resumen global ampliado.
- `AdminManagementPage` permite gestion minima de usuarios, profesionales y reservas.

## Migraciones

No hay migracion. `AuditLog` ya existe.

## Auditoria

Se registran:

- `admin_user_updated`
- `admin_professional_updated`
- `admin_appointment_status_updated`

Los metadatos guardan solo nombres de campos o estado, sin secretos ni notas privadas.
