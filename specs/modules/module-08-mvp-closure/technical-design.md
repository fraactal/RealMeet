# Diseno tecnico del Modulo 8

## Estrategia

El modulo no introduce una nueva arquitectura. Se limita a revisar la integracion existente y corregir inconsistencias concretas entre codigo, contratos, frontend y documentacion.

## Componentes revisados

### Backend

- Routers FastAPI en `backend/app/api/routes`.
- Dependencias de autenticacion y rol en `backend/app/core/deps.py`.
- Schemas de respuesta en `backend/app/schemas`.
- Servicios de negocio en `backend/app/services`.
- Configuracion en `backend/app/core/config.py`.
- Bootstrap con migraciones y seed en `backend/app/bootstrap.py`.

### Frontend

- Router en `frontend/src/routes/router.tsx`.
- Guardia de sesion y roles en `frontend/src/routes/RequireAuth.tsx`.
- Cliente HTTP y queries en `frontend/src/api`.
- Tipos de reservas, dashboards y admin en `frontend/src/types/index.ts`.
- Paginas publicas, cliente, profesional y admin en `frontend/src/pages`.

### Base de datos

- Migraciones Alembic lineales:
  - `20260611_0001_initial`
  - `20260714_0002_catalog_constraints`
  - `20260714_0003_appointment_active_slot_constraints`
- Seed local idempotente en `backend/app/seed/run.py`.

## Decisiones aplicadas

- No se crean migraciones porque no hay cambio de esquema.
- No se agregan dependencias.
- No se modifica seguridad con reglas nuevas; se valida la politica existente.
- El admin no recibe `professional_private_notes` porque no hay politica explicita para exponerlas.
- El profesional conserva acceso a sus notas privadas mediante contrato profesional y autorizacion por propietario.
- La preparacion para staging se documenta como checklist, sin ejecutar despliegue ni provisionar infraestructura.

## Contratos criticos

| Contexto | Contrato | Datos privados |
| --- | --- | --- |
| Cliente | `AppointmentClientRead` | Sin `professional_private_notes`. |
| Profesional | `AppointmentProfessionalRead` | Incluye notas solo para profesional propietario. |
| Admin | `AppointmentAdminRead` | Sin `professional_private_notes`. |
| Publico | Profesionales, categorias, especialidades, slots | Sin hashes, tokens, notas, emails privados ni telefonos. |

## Correcciones previstas

- Alinear README con contratos y rutas actuales.
- Crear documentacion SDD del cierre MVP.
- Actualizar trazabilidad con `M8-MVP-CLOSURE`.

## Riesgos de seguridad pendientes

| Riesgo | Impacto | Prioridad | Mitigacion futura |
| --- | --- | --- | --- |
| Token en `localStorage`. | Exposicion ante XSS. | Alta | Migrar a cookies `HttpOnly`/`SameSite` y revisar CSRF. |
| Swagger habilitado en entornos no productivos. | Exposicion de superficie API si se publica sin control. | Media | Deshabilitar o proteger docs en staging/productivo. |
| CORS permisivo por configuracion incorrecta. | Acceso desde origen no esperado. | Alta | Restringir CORS por ambiente y validar en deploy. |
| Credenciales demo activas. | Acceso no deseado si staging queda publico. | Alta | Deshabilitar o rotar usuarios demo antes de staging publico. |
| Falta rate limiting. | Riesgo de abuso de login/API. | Media | Agregar limites por IP/usuario. |
| Falta hardening Docker/headers. | Menor defensa en profundidad. | Media | Agregar headers, usuario no root y politicas runtime. |
| Sin pentesting/SAST/SCA completo. | Vulnerabilidades no detectadas. | Alta | Ejecutar controles de seguridad antes de produccion. |
| No hay backups/rollback automatizados. | Perdida de datos ante falla. | Alta | Definir backups, restore drills y plan de rollback. |
