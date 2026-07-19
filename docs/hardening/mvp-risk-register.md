# RealMeet - Registro de riesgos del MVP

Este registro acompana el cierre funcional del MVP y orienta la fase de hardening. No implica que los riesgos esten materializados.

| ID | riesgo | probabilidad | impacto | mitigacion | contingencia | owner sugerido | fase objetivo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | Dependencia de servicios externos para Meet, WhatsApp, Google Workspace, n8n y pagos | media | alto | Validar sandbox, timeouts, fallback y runbooks por proveedor | Desactivar proveedor y operar con mock/email/manual | Backend/Ops | H5 |
| R-002 | OAuth administrativo/global limita escenarios multi-tenant | media | medio | Mantener como limitacion aceptada y definir modelo comercial antes de redisenar | Operar con cuenta administrativa hasta piloto acotado | Producto/Backend | H7 |
| R-003 | Operaciones sincronicas pueden degradar UX administrativa | media | medio | Medir latencias y mover tareas lentas a workers cuando haya volumen | Ejecutar retry/reconcile manual en ventanas controladas | Backend | H3 |
| R-004 | Ausencia de workers/colas impide retries automaticos robustos | alta | medio | Introducir scheduler/cola para pagos, webhooks y notificaciones si piloto lo requiere | Runbooks manuales y alertas | Backend/Ops | H3 |
| R-005 | Webhooks externos pueden fallar, duplicarse o llegar tarde | media | alto | Firma, idempotencia, alertas, retencion y pruebas sandbox | Reconcile manual y reenvio controlado | Backend/Ops | H5 |
| R-006 | Pagos sandbox/controlados no reflejan todos los casos productivos | media | alto | Matriz Mercado Pago sandbox, prueba de webhook y decision explicita para piloto | Mantener pagos fake o sandbox durante piloto | Producto/Backend | H5 |
| R-007 | Reembolsos y reconcile manuales generan carga operativa | media | alto | Runbook, alertas e historial auditado | Pausar cobros reales y resolver manualmente | Finanzas/Ops | H3 |
| R-008 | Secretos mal provisionados bloquean arranque o exponen credenciales | media | alto | Secret manager, validaciones startup, rotacion y checklist | Rotar secreto, revocar credencial, redeploy | DevOps | H0 |
| R-009 | Base de datos staging/productiva sin backup probado | media | alto | Backups automaticos y restore probado | Restaurar ultimo backup valido o congelar cambios | DevOps | H4 |
| R-010 | Falta de observabilidad retrasa diagnostico de incidentes | alta | alto | Logs estructurados, correlation IDs, metricas y alertas | Revisar logs plataforma y operar manualmente | DevOps | H3 |
| R-011 | Falta de CI/CD permite regresiones en `staging` | alta | alto | Pipeline PR y deploy staging con smoke tests | Revertir PR o rollback de imagen | DevOps | H1 |
| R-012 | Ausencia de E2E deja huecos entre frontend y backend | media | alto | Automatizar flujos login/reserva/pagos/integraciones criticas | Smoke manual antes de cada release | QA/Dev | H5 |
| R-013 | Bundle frontend grande afecta carga inicial | media | medio | Code splitting, medicion de bundle y performance budget | Priorizar desktop/staging hasta optimizar | Frontend | H6 |
| R-014 | Procesos manuales no documentados escalan mal durante piloto | media | medio | Runbooks, owners y checklist de soporte | Reducir usuarios piloto y centralizar soporte | Ops | H3 |
| R-015 | Privacidad/cumplimiento insuficiente para datos de salud o legales | media | alto | Terminos, privacidad, retencion, minimizacion y revision legal | Limitar piloto a datos sinteticos o consentimiento explicito | Legal/Producto | H7 |
| R-016 | Vulnerabilidades de dependencias no monitoreadas automaticamente | media | medio | SCA en CI y upgrades controlados | Mitigar por configuracion o rollback de version | DevOps/Frontend | H2 |
