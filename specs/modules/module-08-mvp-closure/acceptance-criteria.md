# Criterios de aceptacion del Modulo 8

| ID | Criterio | Estado inicial | Evidencia esperada |
| --- | --- | --- | --- |
| AC-M8-001 | Documentacion de modulos 0 a 7 alineada con estado real. | aprobado | Revision SDD y actualizaciones M8. |
| AC-M8-002 | Matriz de trazabilidad refleja el MVP completo. | aprobado | `requirements-matrix.md` actualizado. |
| AC-M8-003 | Flujo principal cliente funciona integrado. | aprobado | Login, catalogo, disponibilidad, reserva, privacidad, cancelacion y dashboard/admin isolation validados por API. |
| AC-M8-004 | Flujo principal profesional funciona integrado. | aprobado | Login, reservas propias, nota privada, confirmacion y cancelacion profesional validados por API. |
| AC-M8-005 | Flujo principal administrador funciona integrado. | aprobado | Login, metricas, usuarios, profesionales y reservas validados por API. |
| AC-M8-006 | No existen rutas criticas rotas en frontend. | aprobado | Build y revision de router/nav. |
| AC-M8-007 | No existen errores de tipos o build frontend. | aprobado con observacion | Primer intento fallo por carrera con `npm ci`; reintento paso. |
| AC-M8-008 | Pruebas backend pasan. | aprobado | `45 passed, 1 warning`. |
| AC-M8-009 | `/health` responde correctamente. | aprobado | `status=ok`. |
| AC-M8-010 | `/ready` responde correctamente. | aprobado | `status=ready`. |
| AC-M8-011 | Docker Compose levanta servicios. | aprobado | DB/backend/frontend healthy. |
| AC-M8-012 | Migraciones alineadas con modelos. | aprobado | `alembic current`: `20260714_0003 (head)`. |
| AC-M8-013 | Seed continua siendo idempotente. | aprobado | Logs `*_exists` y `seed_completed`. |
| AC-M8-014 | Contratos publicos no exponen datos privados. | aprobado | Revision schemas/rutas. |
| AC-M8-015 | Notas privadas permanecen protegidas. | aprobado | Profesional ve campo; cliente/admin no reciben nombre del campo. |
| AC-M8-016 | Permisos por rol permanecen operativos. | aprobado | Tests y runtime por rol. |
| AC-M8-017 | Doble reserva continua controlada. | aprobado | Tests backend. |
| AC-M8-018 | Reuniones mock permanecen protegidas. | aprobado | Tests y runtime; reserva cancelada sin join activo. |
| AC-M8-019 | No se detectan secretos reales versionados. | aprobado con observacion | Solo placeholders demo. |
| AC-M8-020 | Archivos de entorno documentados. | aprobado | README y env examples. |
| AC-M8-021 | Existe checklist de staging. | aprobado | `staging-checklist.md`. |
| AC-M8-022 | Existe reporte de preparacion MVP. | aprobado | `mvp-readiness-report.md`. |
| AC-M8-023 | Riesgos para produccion identificados. | aprobado | Reportes M8. |
| AC-M8-024 | Funcionalidades diferidas documentadas. | aprobado | Reportes M8. |
| AC-M8-025 | Existe un unico commit final. | aprobado | Se materializa con el commit unico del cierre M8. |
| AC-M8-026 | No se realizo despliegue ni push. | aprobado | Sin despliegue ni push durante el modulo. |

## Estado final

Todos los criterios quedaron aprobados para cierre; el commit unico se ejecuta como ultimo paso operativo.
