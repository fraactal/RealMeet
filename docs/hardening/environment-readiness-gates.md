# RealMeet - Gates de preparacion por ambiente

Estados:

- `cumple`: evidencia suficiente en repo/reviews.
- `parcial`: existe base tecnica, pero falta operacion o automatizacion.
- `pendiente`: no hay evidencia suficiente o requiere trabajo futuro.

## Desarrollo local

| criterio | evidencia requerida | responsable sugerido | estado actual |
| --- | --- | --- | --- |
| Docker operativo | `docker compose up --build` levanta `db`, `backend`, `frontend`; healthchecks healthy | Dev | cumple: validado en reviews MVP |
| Migraciones | `alembic upgrade head`, un solo head, migracion desde base vacia | Backend | cumple: reviews reportan head unico y migracion desde cero |
| Tests principales | suite backend verde | Backend | cumple: review final reporta `272 passed, 1 warning` |
| Frontend build | `npm run build` exitoso | Frontend | cumple: reviews reportan build correcto |
| Fakes habilitados | meeting mock, email log, providers fake/sandbox | Backend | cumple: README y closeout |
| Documentacion basica | README, `.env.example`, credenciales demo y troubleshooting | Dev | cumple |
| Seed local | seed idempotente con admin/profesional/cliente demo | Backend | cumple |

## Staging

| criterio | evidencia requerida | responsable sugerido | estado actual |
| --- | --- | --- | --- |
| Configuracion separada | `APP_ENV=staging`, `.env` externo, variables por ambiente | DevOps | pendiente |
| Secretos externos | `SECRET_KEY`, SMTP, Google, WhatsApp, Mercado Pago fuera de Git | DevOps | pendiente |
| Dominio HTTPS | dominio frontend/backend con TLS valido | DevOps | pendiente |
| Base administrada o protegida | PostgreSQL persistente con acceso restringido | DevOps | pendiente |
| Backups | backup programado y prueba de restore aislada | DevOps/Backend | pendiente |
| Migraciones controladas | procedimiento de `alembic upgrade head`, backup previo y rollback | Backend/DevOps | parcial: migraciones validas localmente |
| Health/readiness | `/health` y `/ready` expuestos y monitoreados | Backend/DevOps | parcial: endpoints existen |
| Logs | stdout capturado por plataforma; sin secretos | DevOps | parcial: logs basicos existen |
| Smoke tests | health, ready, login por rol, catalogo, disponibilidad, reserva | QA/Dev | pendiente |
| Integraciones sandbox | matriz Google/WhatsApp/n8n/Workspace configurada con cuentas sandbox | Backend/Ops | pendiente |
| Mercado Pago sandbox | credenciales sandbox y webhook publico firmado validado | Backend/Ops | pendiente |
| Correo controlado | SMTP sandbox/log con remitente controlado | Ops | pendiente |
| Aislamiento de datos | datos demo o sinteticos; sin datos productivos | Ops | pendiente |
| Rollback documentado | imagen anterior, migracion y restore documentados | DevOps | pendiente |

## Piloto controlado

| criterio | evidencia requerida | responsable sugerido | estado actual |
| --- | --- | --- | --- |
| Usuarios reales limitados | lista cerrada de profesionales/clientes y criterios de entrada | Producto/Ops | pendiente |
| Monitoreo | logs, metricas, errores, latencia y dashboards minimos | DevOps | pendiente |
| Soporte | canal, SLA inicial y owners por incidente | Ops | pendiente |
| Alertas minimas | errores 5xx, pagos fallidos, webhooks fallidos, DB no lista | DevOps | pendiente |
| Backups verificados | restore probado con evidencia fechada | DevOps | pendiente |
| Terminos y privacidad | documentos legales aprobados para datos reales | Legal/Producto | pendiente |
| Operaciones manuales | runbooks de reservas, pagos, refunds, integraciones y usuarios | Ops/Backend | pendiente |
| Pagos controlados | decision explicita: sandbox o produccion limitada; runbook de refunds | Producto/Finanzas | pendiente |
| E2E criticos | pruebas login/reserva/pago fake y sandbox Mercado Pago | QA/Dev | pendiente |

## Produccion

| criterio | evidencia requerida | responsable sugerido | estado actual |
| --- | --- | --- | --- |
| Seguridad aprobada | revision auth/authz, secretos, headers, CORS, rate limit, webhooks | Seguridad/Backend | pendiente |
| Secretos productivos | secret manager, rotacion, owners y auditoria | DevOps | pendiente |
| Backups y restore probado | restore productivo ensayado en entorno aislado | DevOps | pendiente |
| Monitoreo | metricas SLO, logs centralizados, trazas o correlation IDs | DevOps | pendiente |
| Alertas | alertas accionables con responsables | DevOps/Ops | pendiente |
| CI/CD | pipelines PR, staging y produccion con aprobacion manual | DevOps | pendiente |
| Rollback | rollback de imagen/config/migracion probado | DevOps/Backend | pendiente |
| E2E critica | suite E2E estable para flujos de ingreso, reserva, pago e integraciones | QA | pendiente |
| Pruebas de carga | escenarios de busqueda, disponibilidad, reserva y pagos | Backend/QA | pendiente |
| Integraciones productivas | Google, WhatsApp, correo, Mercado Pago y webhooks con credenciales reales | Backend/Ops | pendiente |
| Politicas legales | privacidad, terminos, retencion, soporte y cumplimiento aplicable | Legal/Producto | pendiente |
| Continuidad operacional | runbooks, guardias o responsable de incidentes y plan de comunicacion | Ops | pendiente |
