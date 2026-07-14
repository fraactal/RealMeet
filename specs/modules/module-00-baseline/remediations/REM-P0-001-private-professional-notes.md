# REM-P0-001: Evitar exposicion de notas privadas del profesional

## Identificador

`REM-P0-001` / `SEC-PRIV-001`

## Contexto

Durante el Modulo 0 se detecto que el contrato unico `AppointmentRead` incluia `professional_private_notes` y era usado por endpoints de reservas accesibles por clientes, profesionales y administradores.

## Problema

Las notas privadas del profesional podian serializarse en respuestas genericas de reservas. El riesgo no estaba limitado al frontend: el backend declaraba el campo en el schema de salida.

## Riesgo

Un cliente autenticado podia recibir el nombre del campo `professional_private_notes` y su valor, `null` o cadena vacia al consultar reservas propias, detalle o cancelar una reserva. Esto incumple la regla de negocio de privacidad.

## Actores afectados

- Cliente o paciente: no debe recibir notas privadas.
- Profesional propietario: puede ver y actualizar sus notas privadas en flujos profesionales existentes.
- Administrador: no tenia una politica explicita de acceso a notas privadas; se aplico menor privilegio y no se exponen.
- Usuario publico/no autenticado: no existen endpoints publicos de reservas y no debe ver notas privadas.

## Comportamiento actual encontrado

| Endpoint | Rol autorizado | Schema anterior | Podia incluir notas privadas |
| --- | --- | --- | --- |
| `POST /api/v1/appointments` | Client | `AppointmentRead` | Si |
| `GET /api/v1/appointments/me` | Client, Professional, Admin autenticado | `list[AppointmentRead]` | Si |
| `GET /api/v1/appointments/{appointment_id}` | Actor propietario o Admin | `AppointmentRead` | Si |
| `PATCH /api/v1/appointments/{appointment_id}/cancel` | Actor propietario o Admin | `AppointmentRead` | Si |
| `PATCH /api/v1/appointments/professional/{appointment_id}/confirm` | Professional propietario | `AppointmentRead` | Si |
| `PATCH /api/v1/appointments/professional/{appointment_id}/complete` | Professional propietario | `AppointmentRead` | Si |
| `GET /api/v1/admin/appointments` | Admin | `list[AppointmentRead]` | Si |

Ademas, `AppointmentStatusUpdate` aceptaba `professional_private_notes` y `AppointmentService.transition` lo copiaba sin restringir por rol, por lo que un cliente podia intentar modificarlo al cancelar.

## Comportamiento esperado

- Los contratos para cliente no declaran `professional_private_notes`.
- Los contratos para administrador no declaran `professional_private_notes` porque no existe politica explicita que autorice su visibilidad.
- El contrato profesional declara `professional_private_notes` solo para respuestas de reservas a las que el profesional propietario ya esta autorizado.
- Un cliente no puede actualizar notas privadas mediante payload de cancelacion.

## Alcance

- Separar contratos de salida de reservas por contexto:
  - `AppointmentClientRead`
  - `AppointmentProfessionalRead`
  - `AppointmentAdminRead`
- Actualizar endpoints de reservas y admin para usar contratos seguros.
- Restringir escritura de `professional_private_notes` en transiciones a rol `professional`.
- Separar el payload profesional `AppointmentProfessionalStatusUpdate` del payload generico `AppointmentStatusUpdate`.
- Revisar frontend y confirmar que no depende del campo.
- Actualizar trazabilidad y validaciones.

## Exclusiones

- No se modifico base de datos.
- No se creo migracion.
- No se redisenaron flujos de reservas.
- No se agregaron permisos nuevos.
- No se implemento Modulo 1.
- No se agrego suite de pruebas API ni E2E.

## Criterios de aceptacion

| Criterio | Estado | Evidencia |
| --- | --- | --- |
| AC-REM-P0-001 | aprobado por inspeccion estatica | `AppointmentClientRead` no contiene el campo; `GET /appointments/me` serializa por rol. |
| AC-REM-P0-002 | aprobado por inspeccion estatica | `GET /appointments/{id}` usa `serialize_appointment_for_user`. |
| AC-REM-P0-003 | aprobado por inspeccion estatica | El schema cliente no declara el nombre del campo. |
| AC-REM-P0-004 | aprobado por inspeccion estatica | No existen endpoints publicos de reservas; endpoints autenticados usan contratos seguros. |
| AC-REM-P0-005 | aprobado por inspeccion estatica | `AppointmentProfessionalRead` conserva el campo para profesional propietario. |
| AC-REM-P0-006 | aprobado por inspeccion estatica | `AppointmentService.get_for_actor` bloquea profesionales no propietarios. |
| AC-REM-P0-007 | aprobado | Admin usa `AppointmentAdminRead` sin notas; no se agregaron permisos. |
| AC-REM-P0-008 | aprobado | `AppointmentClientRead` hereda de base sin notas. |
| AC-REM-P0-009 | aprobado | Tipo TS `Appointment` no contiene `professional_private_notes`. |
| AC-REM-P0-010 | aprobado por inspeccion estatica; runtime bloqueado | No quedan usos de `AppointmentRead`; Python no esta disponible para levantar backend o ejecutar pytest. |
| AC-REM-P0-011 | aprobado | No hubo cambios en modelos, Alembic ni DB. |
| AC-REM-P0-012 | aprobado | Matriz actualizada con `SEC-PRIV-001`. |

## Diseno tecnico aplicado

Se reemplazo el contrato unico inseguro por una base sin notas privadas:

- `AppointmentBaseRead`: campos comunes sin `professional_private_notes`.
- `AppointmentClientRead`: respuesta para cliente.
- `AppointmentAdminRead`: respuesta admin bajo menor privilegio.
- `AppointmentProfessionalRead`: extiende base e incluye `professional_private_notes`.

En `backend/app/api/routes/appointments.py` se agrego `serialize_appointment_for_user`, que selecciona el contrato segun rol. En endpoints profesionales dedicados se usa directamente `AppointmentProfessionalRead`. En `backend/app/api/routes/admin.py` se usa `AppointmentAdminRead`.

En `backend/app/services/appointments.py`, `transition` solo copia `professional_private_notes` cuando `user.role` es `professional`. El endpoint generico `PATCH /appointments/{appointment_id}/cancel` usa `AppointmentStatusUpdate`, que no declara notas privadas. Los endpoints profesionales dedicados usan `AppointmentProfessionalStatusUpdate`.

## Endpoints revisados despues de la correccion

| Endpoint | Rol autorizado | Schema posterior | Puede incluir notas privadas |
| --- | --- | --- | --- |
| `POST /api/v1/appointments` | Client | `AppointmentClientRead` | No |
| `GET /api/v1/appointments/me` | Client | `AppointmentClientRead` via serializer | No |
| `GET /api/v1/appointments/me` | Professional propietario | `AppointmentProfessionalRead` via serializer | Si |
| `GET /api/v1/appointments/me` | Admin | `AppointmentAdminRead` via serializer | No |
| `GET /api/v1/appointments/{appointment_id}` | Client propietario | `AppointmentClientRead` via serializer | No |
| `GET /api/v1/appointments/{appointment_id}` | Professional propietario | `AppointmentProfessionalRead` via serializer | Si |
| `GET /api/v1/appointments/{appointment_id}` | Admin | `AppointmentAdminRead` via serializer | No |
| `PATCH /api/v1/appointments/{appointment_id}/cancel` | Client propietario | `AppointmentClientRead` via serializer | No |
| `PATCH /api/v1/appointments/{appointment_id}/cancel` | Professional propietario | `AppointmentProfessionalRead` via serializer | Si |
| `PATCH /api/v1/appointments/{appointment_id}/cancel` | Admin | `AppointmentAdminRead` via serializer | No |
| `PATCH /api/v1/appointments/professional/{appointment_id}/confirm` | Professional propietario | `AppointmentProfessionalRead` | Si |
| `PATCH /api/v1/appointments/professional/{appointment_id}/complete` | Professional propietario | `AppointmentProfessionalRead` | Si |
| `GET /api/v1/admin/appointments` | Admin | `list[AppointmentAdminRead]` | No |

## Archivos modificados

- `backend/app/schemas/appointments.py`
- `backend/app/api/routes/appointments.py`
- `backend/app/api/routes/admin.py`
- `backend/app/services/appointments.py`
- `specs/modules/module-00-baseline/implementation-status.md`
- `specs/modules/module-00-baseline/validation-report.md`
- `specs/traceability/requirements-matrix.md`

## Validaciones realizadas

- Busqueda de todas las referencias a `professional_private_notes`.
- Busqueda de todas las referencias a `AppointmentRead`.
- Revision de endpoints de reservas y admin.
- Revision de tipos TypeScript y componentes de reservas.
- Confirmacion de que `AppointmentRead` ya no se usa en backend/frontend.
- Confirmacion de que `AppointmentStatusUpdate` generico ya no declara `professional_private_notes`.
- Intento de validacion Python fuera del sandbox: bloqueado porque Python no esta disponible en PATH.

## Resultado final

La exposicion por contrato generico queda corregida. Clientes y administradores reciben contratos sin `professional_private_notes`. Profesionales autorizados conservan acceso en flujos existentes. No se modifico base de datos.

## Deuda tecnica pendiente

- Ejecutar validacion runtime cuando el entorno Python/Docker este disponible.
- Agregar una prueba automatizada minima de regresion para cliente cuando pytest funcione localmente.
- Revisar reglas completas de transicion de estados y cancelacion en un modulo posterior.
