# Criterios de aceptacion del Modulo 6

| ID | Criterio | Estado |
| --- | --- | --- |
| AC-M6-001 | El sistema usa `MeetingProvider` y no acopla reservas a Google o Zoom. | implementado |
| AC-M6-002 | `MockMeetingProvider` crea datos de reunion simulados. | implementado |
| AC-M6-003 | Una reserva remota obtiene informacion de reunion. | implementado |
| AC-M6-004 | Una reserva presencial no obtiene enlace remoto. | implementado |
| AC-M6-005 | Cliente y profesional asociados consultan datos de reunion. | implementado |
| AC-M6-006 | Usuario ajeno no consulta el enlace por API. | implementado |
| AC-M6-007 | Reserva cancelada no presenta reunion activa. | implementado |
| AC-M6-008 | Modo desarrollo funciona sin SMTP real. | implementado |
| AC-M6-009 | Modo SMTP usa configuracion externa. | implementado |
| AC-M6-010 | Logs no muestran password SMTP ni secretos. | implementado |
| AC-M6-011 | Creacion genera notificacion basica. | implementado |
| AC-M6-012 | Confirmacion genera notificacion basica. | implementado |
| AC-M6-013 | Cancelacion genera notificacion basica. | implementado |
| AC-M6-014 | Notificaciones no contienen notas privadas. | implementado |
| AC-M6-015 | Fallo de correo no revierte reserva valida. | implementado |
| AC-M6-016 | Contratos no exponen configuracion tecnica ni secretos. | implementado |
| AC-M6-017 | Frontend cliente muestra datos de reunion autorizados. | implementado |
| AC-M6-018 | Frontend profesional muestra datos de reunion autorizados. | implementado |
| AC-M6-019 | No se implementan integraciones reales con Google o Zoom. | implementado |
| AC-M6-020 | No se implementa WhatsApp, SMS ni push. | implementado |
| AC-M6-021 | `/health` y `/ready` continuan operativos. | aprobado |
| AC-M6-022 | Pruebas minimas pasan. | aprobado |
| AC-M6-023 | Frontend compila. | aprobado |
| AC-M6-024 | Trazabilidad actualizada. | aprobado |
| AC-M6-025 | Existe un unico commit final. | aprobado al cierre |
| AC-M6-026 | No se avanzo al Modulo 7. | implementado |
