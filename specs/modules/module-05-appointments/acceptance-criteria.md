# Criterios de aceptacion del Modulo 5

| ID | Criterio | Estado |
| --- | --- | --- |
| AC-M5-001 | Cliente crea reserva usando slot disponible. | implementado |
| AC-M5-002 | Backend revalida el slot antes de reservar. | implementado |
| AC-M5-003 | No se reserva horario pasado. | implementado |
| AC-M5-004 | No se reserva fuera de disponibilidad. | implementado |
| AC-M5-005 | No se reserva horario bloqueado. | implementado |
| AC-M5-006 | No se reserva horario ocupado. | implementado |
| AC-M5-007 | Dos solicitudes del mismo horario no crean dos activas. | implementado |
| AC-M5-008 | Conflicto de slot responde controlado. | implementado |
| AC-M5-009 | Creacion registra historial inicial. | implementado |
| AC-M5-010 | Cliente lista sus reservas. | implementado |
| AC-M5-011 | Cliente no consulta reservas ajenas. | implementado |
| AC-M5-012 | Cliente cancela reserva propia futura. | implementado |
| AC-M5-013 | Cliente no confirma ni completa. | implementado |
| AC-M5-014 | Profesional lista sus reservas. | implementado |
| AC-M5-015 | Profesional no gestiona reservas ajenas. | implementado |
| AC-M5-016 | Profesional confirma reserva pendiente. | implementado |
| AC-M5-017 | Profesional cancela reserva valida. | implementado |
| AC-M5-018 | Profesional completa reserva confirmada. | implementado |
| AC-M5-019 | Profesional marca no show desde reserva confirmada. | implementado |
| AC-M5-020 | Transiciones invalidas se rechazan. | implementado |
| AC-M5-021 | Toda transicion registra historial. | implementado |
| AC-M5-022 | Profesional propietario administra notas privadas. | implementado |
| AC-M5-023 | Cliente nunca recibe `professional_private_notes`. | implementado |
| AC-M5-024 | Admin no recibe notas privadas por defecto. | implementado |
| AC-M5-025 | Cancelacion libera el slot. | implementado |
| AC-M5-026 | `pending` y `confirmed` bloquean slots. | implementado |
| AC-M5-027 | Contratos no exponen hashes, tokens ni internos. | implementado |
| AC-M5-028 | Frontend cliente permite reservar, listar y cancelar. | implementado |
| AC-M5-029 | Frontend profesional permite gestionar estados y notas. | implementado |
| AC-M5-030 | `/health` y `/ready` operativos. | aprobado |
| AC-M5-031 | Frontend compila. | aprobado |
| AC-M5-032 | Pruebas minimas pasan. | aprobado |
| AC-M5-033 | Trazabilidad actualizada. | aprobado |
| AC-M5-034 | Existe un unico commit final. | aprobado al cierre |
| AC-M5-035 | No se implementaron correos avanzados, pagos ni reuniones reales. | implementado |
