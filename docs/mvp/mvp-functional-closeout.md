# RealMeet - Cierre funcional del MVP

## Capacidades funcionales
RealMeet cuenta con las capacidades funcionales principales del MVP:
- Autenticacion con JWT.
- Roles `admin`, `professional` y `client`.
- Perfiles de cliente y profesional.
- Catalogo de categorias y especialidades.
- Disponibilidad semanal, bloqueos y calculo de slots.
- Reservas con historial y estados operativos.
- Google Meet preparado mediante integracion desacoplada y fallback/mock.
- WhatsApp Cloud preparado con consentimiento, plantillas, mensajes y webhooks.
- Email transaccional mediante servicio desacoplado.
- Webhooks salientes con firma e historial de entregas.
- n8n para automatizaciones externas controladas.
- Calendarios externos y deteccion de conflictos.
- Google Workspace administrativo/global.
- Google Sheets para exportaciones sincronas.
- Google Docs para plantillas y documentos generados.
- Automatizacion documental asociada a eventos de reserva.
- Pagos internos con ordenes, historial e idempotencia.
- Mercado Pago Checkout Pro por redireccion y webhook firmado.
- Reembolsos administrativos totales/parciales y reconcile manual.

## Flujo principal
```text
cliente
-> profesional
-> disponibilidad
-> reserva
-> pago
-> confirmacion
-> reunion
-> notificacion
-> calendario
-> automatizacion
-> documento
```

## Estado tecnico
- Backend: FastAPI, SQLAlchemy 2, Pydantic, servicios de dominio y routers por rol.
- Frontend: React, Vite, TypeScript, rutas protegidas y vistas operativas para admin/profesional/cliente.
- Base de datos: PostgreSQL.
- Migraciones: Alembic.
- Infraestructura local: Docker Compose.
- Health: `/health`.
- Readiness: `/ready`.
- Tests: suites especificas por modulo y pruebas acotadas de pagos para cierre.
- Staging existente: preparado para integracion posterior, sin despliegue realizado en este cierre.

## Limitaciones aceptadas
- OAuth Google administrativo/global.
- Uso de fakes para integraciones externas cuando corresponde.
- Sin transaccion distribuida.
- Retry/reconcile manual.
- Sin workers.
- Sin scheduler.
- Sin colas.
- Sin sync bidireccional completo.
- Sheets sincrono.
- Email sin adjuntos.
- Mercado Pago en sandbox/configuracion controlada.
- Sin produccion real.
- Sin facturacion.
- Sin boletas.
- Sin impuestos.
- Sin conciliacion bancaria.
- Sin chargebacks completos.
- Warning Vite de chunk grande aceptado para MVP.
- Warning passlib/crypt aceptado para MVP.

## Fase siguiente
Despues del MVP comienza una fase separada de:
```text
mejoras
deuda tecnica
seguridad profunda
performance
observabilidad
CI/CD
E2E
responsive
accesibilidad
staging real
preparacion productiva
```

Estos puntos no se corrigen en el cierre funcional del MVP.

## Declaracion
El MVP de RealMeet queda funcionalmente cerrado. El sistema cubre el recorrido operacional principal desde busqueda y reserva hasta pago, confirmacion, reunion, notificacion, calendario, automatizacion documental y reembolso manual. No se declara listo para produccion real sin la fase posterior de hardening y preparacion productiva.
