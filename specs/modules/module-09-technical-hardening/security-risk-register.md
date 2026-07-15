# Registro de riesgos de seguridad

| Riesgo | Estado M9 | Impacto | Prioridad | Mitigacion futura |
| --- | --- | --- | --- | --- |
| Token en `localStorage` | residual | XSS podria exfiltrar token | Alta | Migrar a cookies HttpOnly/SameSite y revisar CSRF. |
| Rate limiter en memoria | parcialmente mitigado | No protege multi-instancia | Alta | Redis, gateway o WAF. |
| Sin HTTPS/dominio | residual | Trafico no protegido si se publica sin TLS | Alta | Configurar TLS antes de staging publico. |
| Swagger expuesto por mala configuracion | mitigado configurable | Superficie API publica | Media | `ENABLE_DOCS=false` en staging publico/production o proteccion adicional. |
| Credenciales demo | mitigado configurable | Acceso no deseado | Alta | `ENABLE_DEMO_SEED=false`, desactivar/rotar usuarios demo. |
| Vulnerabilidades npm | residual | Riesgo runtime/build segun paquete | Alta | Upgrade controlado, SCA automatizado. |
| Sin SAST/secret scanning completo | residual | Hallazgos no detectados | Media | Integrar SAST, SCA, Trivy y secret scanning. |
| Backups no automatizados | residual | Perdida de datos | Alta | Backups programados y restore drills. |
| Logs debug de email body | residual controlado | Exposicion si se habilita DEBUG/level debug | Media | Redaccion formal y politica de logs. |
| Sin observabilidad/alertas | residual | Incidentes no detectados | Media | Monitoreo, alertas y trazas. |
| Sin hardening clinico/legal | residual | No apto para datos clinicos reales | Alta | Privacidad clinica, cumplimiento y auditoria regulatoria. |
