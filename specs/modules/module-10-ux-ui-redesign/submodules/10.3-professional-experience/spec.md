# Submodulo 10.3 - Experiencia profesional

## Objetivo

Rediseñar la experiencia autenticada del profesional para que RealMeet funcione como una herramienta diaria clara, ordenada y comercialmente vendible, sin cambiar reglas de negocio ni contratos backend.

## Alcance

- Dashboard profesional en `/dashboard`.
- Metricas profesionales en `/dashboard/professional`.
- Reservas profesionales en `/dashboard/professional/appointments`.
- Perfil publico y especialidades en `/dashboard/professional/catalog`.
- Disponibilidad y bloqueos en `/dashboard/professional/availability`.
- Componentes reutilizables especificos del rol profesional.
- Estados de carga, error y vacio.
- Traduccion de estados y fechas `es-CL`.

## Fuera de alcance

- Cambios backend.
- Nuevas APIs.
- Nuevas reglas de reserva o transiciones de estado.
- Reprogramacion.
- Videollamada real.
- Pagos.
- Rediseño cliente, admin, landing o catalogo publico.
- Rediseño global del shell.
- Pruebas E2E.

## Datos disponibles

- `fetchProfessionalMetrics`: conteos, proximas reservas, actividad reciente, perfil publico y reglas activas.
- `fetchProfessionalAppointments`: reservas profesionales, estados, modalidad, reunion, notas privadas e historial.
- `fetchProfessionalPublicProfile`: datos publicos editables.
- `fetchProfessionalSpecialties`: especialidades propias.
- `fetchAvailabilityRules`: reglas semanales.
- `fetchAvailabilityBlocks`: bloqueos manuales.

## Componentes previstos

- `ProfessionalHero`.
- `ProfessionalStatCard`.
- `ProfessionalAppointmentCard`.
- `ProfessionalQuickActions`.
- `ProfessionalConfigStatus`.

## Criterios de aceptacion

| ID | Criterio | Estado |
| --- | --- | --- |
| M10.3-AC-001 | Dashboard profesional prioriza agenda, proximas acciones y configuracion. | Cumplido |
| M10.3-AC-002 | Reservas profesionales usan estados traducidos, fechas legibles y vista compacta. | Cumplido |
| M10.3-AC-003 | Notas privadas e historial no estan siempre expandidos. | Cumplido |
| M10.3-AC-004 | Perfil publico queda organizado en secciones claras. | Cumplido |
| M10.3-AC-005 | Disponibilidad presenta reglas y bloqueos de forma comprensible. | Cumplido |
| M10.3-AC-006 | Metricas profesionales quedan jerarquizadas y sin enums tecnicos. | Cumplido |
| M10.3-AC-007 | Se usan LoadingState, ErrorState y EmptyState. | Cumplido |
| M10.3-AC-008 | Responsive basico funciona en 390-430px. | Cumplido |
| M10.3-AC-009 | Backend, guards y permisos permanecen intactos. | Cumplido |
| M10.3-AC-010 | Frontend compila correctamente. | Cumplido |

## Riesgos

- Las reservas profesionales no incluyen nombre de cliente; la UI debe evitar inventarlo.
- Algunas pantallas comparten datos con futuros submodulos, pero el cambio se limita a rutas profesionales.
- Las metricas disponibles son basicas; no se agregan graficos ni tendencias inexistentes.

## Validacion minima

- `docker-compose exec -T frontend npm run build`.
- Revision manual de dashboard, reservas, perfil, disponibilidad y metricas.
- Revision responsive aproximada 390-430px.
- Capturas representativas.
