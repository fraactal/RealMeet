# Estado de implementacion observado

Fecha de baseline: 2026-07-14.

## Arquitectura encontrada

Backend FastAPI con estructura modular en `backend/app`: `api`, `core`, `db`, `models`, `schemas`, `services`, `repositories`, `meetings`, `emails`, `seed`. Frontend React/Vite con `pages`, `components`, `layouts`, `api`, `routes`, `store`, `types`. Infra local con `docker-compose.yml`, PostgreSQL, backend y frontend containerizados.

## Specs retrospectivas iniciales

### CFG-001 Configuracion y arranque

- Objetivo: cargar variables, configurar CORS, DB, JWT, SMTP, meeting provider y arranque.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: `Settings` con `pydantic-settings`; CORS JSON/CSV; `bootstrap` espera DB, migra, ejecuta seed e inicia Uvicorn.
- Pendiente: no se ejecuto arranque completo por limitaciones de Docker/runtimes locales.
- Archivos: `backend/app/core/config.py`, `backend/app/bootstrap.py`, `.env.example`, `docker-compose.yml`.
- Endpoints: no aplica.
- DB: usa `DATABASE_URL`.
- Controles: inspeccion estatica; `docker-compose config`.
- Deuda/riesgo: faltan `backend/.env.example` y `frontend/.env.example` aunque README los menciona.
- Estado final: `implemented-unverified`.

### HEALTH-001 Health

- Objetivo: exponer salud basica sin depender de DB.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: `GET /health` retorna estado y ambiente; existe test unitario.
- Pendiente: no se pudo ejecutar pytest local.
- Archivos: `backend/app/main.py`, `backend/tests/test_health.py`.
- Endpoints: `GET /health`.
- DB: no aplica.
- Controles: inspeccion estatica.
- Estado final: `implemented-unverified`.

### READY-001 Readiness

- Objetivo: reportar disponibilidad de base de datos.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: `GET /ready` usa `check_database_connection`; test monkeypatch cubre ready/not_ready.
- Pendiente: no validado contra PostgreSQL real.
- Archivos: `backend/app/main.py`, `backend/app/core/runtime.py`, `backend/tests/test_health.py`.
- Endpoints: `GET /ready`.
- DB: requiere conexion.
- Estado final: `implemented-unverified`.

### AUTH-001 Autenticacion

- Objetivo: registro, login JWT y usuario actual.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: `POST /auth/register`, `POST /auth/register-client`, `POST /auth/login`, `GET /auth/me`; password hashing; JWT con expiracion.
- Pendiente: no se validaron flujos manuales ni expiracion real.
- Archivos: `backend/app/api/routes/auth.py`, `backend/app/services/auth.py`, `backend/app/core/security.py`.
- Endpoints: `/api/v1/auth/*`.
- DB: `users`, `client_profiles`.
- Riesgo: `register` permite enviar rol en payload; revisar si el registro publico debe permitir crear admins/professionals sin flujo controlado.
- Estado final: `implemented-unverified`.

### ROLE-001 Autorizacion por roles

- Objetivo: restringir acciones segun rol.
- Estado encontrado: `partial`.
- Criterios cumplidos: `require_roles` aplicado en admin, catalogo write, perfil professional, disponibilidad professional, crear appointment client, metricas.
- Pendiente: validacion manual completa; revisar cancelacion por estado/fecha; frontend no segmenta rutas por rol.
- Archivos: `backend/app/core/deps.py`, routers en `backend/app/api/routes`.
- Endpoints: multiples.
- Riesgo: `AppointmentRead` expone notas privadas; `admin.patch_professional` acepta `dict`.
- Estado final: `partial`.

### PROF-001 Profesionales publicos

- Objetivo: listar y consultar perfiles publicos.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: listado publico con filtros `search`, `category_id`, `specialty_id`; detalle por id; frontend lista profesionales.
- Pendiente: validar manualmente filtros, paginacion y datos expuestos.
- Archivos: `backend/app/api/routes/professionals.py`, `backend/app/services/professionals.py`, `frontend/src/pages/ProfessionalsPage.tsx`.
- Endpoints: `GET /professionals`, `GET /professionals/{id}`.
- Estado final: `implemented-unverified`.

### FRONT-001 Frontend publico

- Objetivo: home, listado de profesionales y login.
- Estado encontrado: `partial`.
- Criterios cumplidos: rutas publicas `/`, `/professionals`, `/login`; cliente Axios con timeout; TanStack Query para profesionales.
- Pendiente: no se pudo ejecutar build; no hay perfil publico detallado ni flujo de reserva en UI.
- Archivos: `frontend/src/routes/router.tsx`, `frontend/src/pages/*.tsx`, `frontend/src/api`.
- Estado final: `partial`.

### FRONT-002 Manejo de errores frontend

- Objetivo: diferenciar red, timeout, API no disponible, credenciales invalidas y errores inesperados.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: `normalizeApiError` clasifica `network`, `timeout`, `unavailable`, `invalid_credentials`, `unauthorized`, `server`, `unexpected`.
- Pendiente: no validado en navegador.
- Archivos: `frontend/src/api/errors.ts`.
- Estado final: `implemented-unverified`.

### INFRA-001 Docker Compose

- Objetivo: levantar DB, backend y frontend con healthchecks.
- Estado encontrado: `verified` para sintaxis con observaciones.
- Criterios cumplidos: `docker-compose config` genera configuracion; servicios, puertos y healthchecks definidos.
- Pendiente: no se ejecuto `up --build`.
- Archivos: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`.
- Riesgo: Docker emite advertencia `Acceso denegado` al leer config de usuario.
- Estado final: `implemented-unverified` para ejecucion completa; `verified` solo para config.

### MIG-001 Migraciones

- Objetivo: crear schema inicial.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: migracion Alembic inicial crea entidades principales y enums.
- Pendiente: no se ejecuto `alembic upgrade head` local.
- Archivos: `backend/alembic/versions/20260611_0001_initial.py`.
- DB: todas las tablas principales.
- Riesgo: no se observaron constraints para evitar doble reserva concurrente.
- Estado final: `implemented-unverified`.

### SEED-001 Seed

- Objetivo: crear usuarios demo, categorias, especialidades, perfil profesional y disponibilidad.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: admin, client, professional; Salud/Legal; especialidades requeridas; disponibilidad lunes a viernes.
- Pendiente: no ejecutado contra DB real.
- Archivos: `backend/app/seed/run.py`.
- Estado final: `implemented-unverified`.

### EMAIL-001 Servicio de correo

- Objetivo: enviar por SMTP o modo desarrollo/log.
- Estado encontrado: `designed`.
- Criterios cumplidos: `EmailService.send` imprime en modo dev sin SMTP; usa SMTP si `SMTP_HOST` existe.
- Pendiente: no hay templates, reintentos, TLS configurable ni eventos para todos los estados; solo se observo envio al crear reserva.
- Archivos: `backend/app/emails/service.py`, `backend/app/services/appointments.py`.
- Estado final: `designed`.

### MEET-001 Capa de reuniones

- Objetivo: usar mock y preparar proveedores reales.
- Estado encontrado: `implemented-unverified`.
- Criterios cumplidos: interfaz, mock operativo, Google/Zoom no implementados intencionalmente, campos en `Appointment`.
- Pendiente: no validado en flujo real; factory siempre retorna mock para cualquier valor.
- Archivos: `backend/app/meetings/*`, `backend/app/services/appointments.py`.
- Estado final: `implemented-unverified`.

### AVAIL-001 Disponibilidad

- Objetivo: reglas semanales, bloqueos y calculo de slots.
- Estado encontrado: `partial`.
- Criterios cumplidos: CRUD basico de reglas/bloqueos para professional; calculo excluye bloqueos y reservas.
- Pendiente: no validado manualmente; `extra_available` no parece generar disponibilidad adicional; reservas canceladas bloquean slots al calcular.
- Archivos: `backend/app/api/routes/availability.py`, `backend/app/services/availability.py`.
- Estado final: `partial`.

### BOOK-001 Reservas

- Objetivo: crear, consultar y cambiar estados de reservas.
- Estado encontrado: `partial`.
- Criterios cumplidos: creacion por cliente; solapamiento profesional en servicio; historial inicial y transiciones; consultas filtradas por actor.
- Pendiente: validar que cliente no duplique bloque; validar slot contra disponibilidad; restricciones de transicion; correos para confirmada/cancelada/completada.
- Archivos: `backend/app/api/routes/appointments.py`, `backend/app/services/appointments.py`, `backend/app/schemas/appointments.py`.
- Remediacion aplicada: `REM-P0-001` separa contratos `AppointmentClientRead`, `AppointmentProfessionalRead` y `AppointmentAdminRead` para evitar exponer `professional_private_notes` a clientes y administradores.
- Estado final: `partial`.

### METRIC-001 Metricas

- Objetivo: metricas profesional/admin.
- Estado encontrado: `partial`.
- Criterios cumplidos: totales basicos, cancelaciones, completadas, clientes unicos, ingresos estimados mensual para profesional; totales admin.
- Pendiente: faltan reservas por estado/categoria, profesionales mas activos, crecimiento mensual, especialidades mas solicitadas.
- Archivos: `backend/app/services/metrics.py`, `backend/app/api/routes/metrics.py`.
- Estado final: `partial`.

### ADMIN-001 Backoffice minimo

- Objetivo: gestion admin de usuarios, profesionales y reservas.
- Estado encontrado: `partial`.
- Criterios cumplidos: listado/edicion usuarios, listado/edicion profesionales, listado reservas bajo dependencia admin.
- Pendiente: frontend admin minimo limitado a metricas; payload profesional generico; falta gestion UI de catalogos/reservas.
- Archivos: `backend/app/api/routes/admin.py`, `frontend/src/pages/AdminMetricsPage.tsx`.
- Estado final: `partial`.

## Backlog priorizado

### P0

- Definir politica de registro: impedir creacion publica de usuarios admin si no corresponde.
- Reforzar reservas contra doble booking con constraint/estrategia transaccional.

### Remediaciones P0 completadas

- `REM-P0-001`: corregida exposicion de `professional_private_notes` mediante contratos de salida por rol/contexto. Pendiente validacion runtime cuando el entorno lo permita.

### P1

- Validar que una reserva se cree solo sobre slots disponibles.
- Completar reglas de transicion de estados y cancelacion de reservas futuras.
- Completar correos para reserva confirmada, cancelada y completada.
- Agregar env examples faltantes o ajustar README.
- Validar migracion y seed en Docker Compose.
- Completar UI de reserva, perfil publico y disponibilidad.
- Completar backoffice MVP de catalogos, usuarios, profesionales y reservas.
- Completar metricas MVP faltantes.

### P2

- Mejorar validaciones Pydantic de rangos, duracion, precio, strings y fechas.
- Reemplazar payload `dict` en admin professional por schema explicito.
- Agregar controles automatizados pequenos para health/readiness/auth cuando haya entorno estable.
- Mejorar observabilidad de errores sin datos sensibles.
- Revisar timezone y limites de consultas de disponibilidad.

### P3

- Robustecimiento clinico posterior al MVP.
- Privacidad avanzada, auditoria y operacion.
- Preparacion comercial, suscripciones y soporte.
- Integraciones reales mediante specs: Google Meet, Zoom, WhatsApp, pagos.

## Roadmap sugerido

- Modulo 1: configuracion, arranque, migraciones, seed, health, readiness y errores base.
- Modulo 2: autenticacion, autorizacion, perfiles y permisos.
- Modulo 3: categorias, especialidades, perfil profesional y busqueda publica.
- Modulo 4: disponibilidad, bloqueos y calculo de slots.
- Modulo 5: reservas, estados, historial, notas privadas y prevencion de dobles reservas.
- Modulo 6: correo, MockMeetingProvider y notificaciones basicas.
- Modulo 7: dashboards, administracion y metricas.
- Modulo 8: cierre funcional MVP, documentacion, validacion integrada y staging.
- Fase posterior: robustecimiento para consultas clinicas, seguridad, privacidad, cumplimiento, operacion, pruebas y preparacion comercial.

## Recomendacion de siguiente modulo

Continuar con Modulo 1 para estabilizar entorno, configuracion, migraciones, seed, health/readiness y documentacion de variables. Sin esa base validada, los modulos funcionales tendran validaciones debiles.
