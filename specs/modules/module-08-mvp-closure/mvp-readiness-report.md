# MVP Readiness Report

## El MVP funcional esta completo?

Si, para desarrollo local y demo controlada. El MVP cubre autenticacion, roles, perfiles, catalogo, disponibilidad, bloqueos, slots, reservas, historial, notas privadas protegidas, reuniones mock, correo en modo log/SMTP opcional, dashboards, metricas y backoffice minimo.

No esta listo para produccion clinica ni uso regulado.

## Flujos validados

- Cliente: login, catalogo, filtros, disponibilidad, reserva, historial, cancelacion y dashboard.
- Profesional: login, perfil publico, especialidades, disponibilidad, bloqueos, reservas, cambios de estado, notas privadas y dashboard.
- Admin: login, metricas, usuarios, profesionales, catalogo, reservas y auditoria minima.

La evidencia runtime final queda en `validation-report.md` y fue aprobada con observaciones menores.

## Funcionalidades diferidas

- Google Meet real.
- Zoom real.
- WhatsApp.
- Pagos, suscripciones y facturacion.
- Recuperacion de contrasena y MFA.
- Ficha clinica, consentimientos, recetas y cumplimiento clinico/legal.
- Multi-tenant avanzado y roles configurables.
- Auditoria regulatoria completa.
- Observabilidad, backups, monitoreo, alertas y rate limiting.

## Riesgos que impiden produccion

- No hay hardening de seguridad productiva.
- No hay HTTPS/dominio ni configuracion cloud.
- No hay pentesting, SAST/SCA completo ni pruebas de carga.
- Token frontend en `localStorage`.
- Credenciales demo y `SECRET_KEY` placeholder deben rotarse.
- Backups, rollback y monitoreo no estan implementados.
- No hay cumplimiento clinico/legal validado.

## Riesgos que permiten staging controlado

- El stack local levanta con Compose y PostgreSQL.
- Los contratos por rol minimizan exposicion de datos sensibles.
- Las migraciones son lineales y el seed es idempotente.
- Email real es opcional; `EMAIL_MODE=log` permite staging tecnico.
- Meeting mock evita depender de integraciones externas.

## Deuda tecnica

- Mejorar almacenamiento de token.
- Agregar rate limiting y headers de seguridad.
- Deshabilitar docs OpenAPI en entornos no controlados.
- Agregar observabilidad, backups y restore drills.
- Ampliar pruebas frontend y API integradas.
- Validar base nueva en entorno temporal aislado.
- Resolver vulnerabilidades reportadas por `npm audit` con upgrades controlados.

## Falta para venderlo como plataforma clinica

- Privacidad clinica formal, consentimiento informado y retencion/eliminacion de datos.
- Auditoria regulatoria y trazabilidad clinica.
- Seguridad productiva completa.
- Contratos legales, terminos, politicas y cumplimiento local.
- Operacion con backups, monitoreo, alertas, soporte y continuidad.
- Integraciones reales seguras si se ofrecen teleconsultas.

## Siguiente fase recomendada

Fase de staging y hardening controlado: secretos reales, CORS restringido, HTTPS, usuarios demo gestionados, SCA/SAST, pruebas integradas, backups, monitoreo basico, rate limiting y decisiones de privacidad clinica antes de produccion.

## Clasificacion de readiness

| Ambito | Clasificacion |
| --- | --- |
| Desarrollo local | Listo. |
| Demo | Listo para demo controlada si se usan datos no reales. |
| Staging | Preparado con checklist previo y secretos seguros. |
| Produccion | No listo. |
| Uso clinico real | No listo. |
