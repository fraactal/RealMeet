# RealMeet

RealMeet es un MVP SaaS para agendamiento de profesionales orientado inicialmente a salud y servicios legales. El proyecto sigue un enfoque de monolito modular: backend FastAPI, frontend React/Vite, PostgreSQL, Docker Compose, migraciones Alembic y seed local.

## Alcance MVP

- Autenticacion JWT con roles `admin`, `professional`, `client`
- Autorizacion backend por rol y restauracion de sesion frontend contra `/auth/me`
- Registro base y acceso por roles
- Catalogo de categorias y especialidades
- Perfil profesional y especialidades asociadas
- Reglas de disponibilidad semanal, bloqueos manuales y calculo publico de slots
- Reserva de horas con validacion de disponibilidad, solapamientos, estados e historial
- Meeting provider mock preparado para futuras integraciones
- Servicio de correo por SMTP o salida a log en desarrollo
- Notificaciones basicas para reserva creada, confirmada y cancelada
- Dashboards por rol y backoffice administrativo minimo
- Metricas basicas para profesional y administrador
- Backoffice minimo para usuarios, profesionales y reservas

## Arquitectura

### Backend

- `app/api`: routers FastAPI
- `app/core`: configuracion, seguridad, scheduler y dependencias
- `app/db`: sesion SQLAlchemy y metadata
- `app/models`: entidades ORM
- `app/schemas`: contratos Pydantic
- `app/services`: logica de negocio
- `app/repositories`: acceso a datos puntual
- `app/meetings`: providers desacoplados
- `app/emails`: servicio de envio de correos
- `app/seed`: seed inicial local

### Frontend

- `src/pages`: pantallas principales
- `src/layouts`: layouts publico y dashboard
- `src/components`: UI reutilizable
- `src/api`: cliente HTTP y consultas
- `src/store`: estado global con Zustand
- `src/routes`: enrutado y proteccion basica
- `src/types`: tipos compartidos de UI

## Modelo base

Entidades incluidas:

- `User`
- `ProfessionalProfile`
- `ClientProfile`
- `Category`
- `Specialty`
- `ProfessionalSpecialty`
- `AvailabilityRule`
- `AvailabilityBlock`
- `Appointment`
- `AppointmentHistory`
- `AuditLog`
- `SystemSetting`

## Endpoints principales

Base API: `http://localhost:18000/api/v1`

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /users/me`
- `PATCH /users/me`
- `GET /users/me/profile`
- `PATCH /users/me/profile`
- `GET /categories`
- `POST /categories`
- `PATCH /categories/{id}`
- `GET /specialties`
- `POST /specialties`
- `PATCH /specialties/{id}`
- `GET /professionals`
- `GET /professionals/{id}`
- `POST /professionals/profile`
- `GET /professionals/me/profile`
- `PATCH /professionals/me/profile`
- `GET /professionals/{id}/availability?date=YYYY-MM-DD`
- `GET /professionals/me/availability-rules`
- `POST /professionals/me/availability-rules`
- `PATCH /professionals/me/availability-rules/{id}`
- `DELETE /professionals/me/availability-rules/{id}`
- `GET /professionals/me/availability-blocks`
- `POST /professionals/me/availability-blocks`
- `PATCH /professionals/me/availability-blocks/{id}`
- `DELETE /professionals/me/availability-blocks/{id}`
- `POST /appointments`
- `GET /appointments/me`
- `GET /appointments/professional/me`
- `GET /appointments/{id}`
- `PATCH /appointments/{id}/cancel`
- `PATCH /appointments/professional/{id}/confirm`
- `PATCH /appointments/professional/{id}/complete`
- `PATCH /appointments/professional/{id}/no-show`
- `PATCH /appointments/professional/{id}/cancel`
- `PATCH /appointments/professional/{id}/private-notes`
- `GET /client/metrics`
- `GET /professional/metrics`
- `GET /admin/metrics`
- `GET /admin/users`
- `GET /admin/users/{id}`
- `PATCH /admin/users/{id}`
- `GET /admin/professionals`
- `GET /admin/professionals/{id}`
- `PATCH /admin/professionals/{id}`
- `GET /admin/appointments`
- `GET /admin/appointments/{id}`
- `PATCH /admin/appointments/{id}/status`

## Flujo funcional principal

1. El cliente inicia sesion.
2. Consulta el listado publico de profesionales.
3. Revisa disponibilidad del profesional.
4. Reserva una hora disponible.
5. El backend revalida disponibilidad, solapamientos y crea la cita.
6. Si corresponde, se genera un meeting mock.
7. Se registra o envia una notificacion basica.
8. La reserva queda disponible para dashboards, metricas e historial.
9. El profesional puede confirmar, cancelar, completar o marcar no show segun transicion valida.

## Variables de entorno

El flujo recomendado con Docker Compose usa el archivo de la raiz:

- `.env.example`

Para ejecucion local fuera de Docker existen ejemplos por subproyecto:

- `backend/.env.example`
- `frontend/.env.example`

Variables backend relevantes:

- `APP_NAME`
- `APP_ENV`
- `DEBUG`
- `API_V1_PREFIX`
- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_FROM_NAME`
- `SMTP_USE_TLS`
- `SMTP_TIMEOUT_SECONDS`
- `EMAIL_MODE`
- `DEFAULT_MEETING_PROVIDER`
- `MOCK_MEETING_BASE_URL`
- `ENABLE_DOCS`
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_MAX_REQUESTS`
- `ENABLE_DEMO_SEED`
- `BACKEND_HOST`
- `BACKEND_PORT`

Variables Docker Compose relevantes:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `BACKEND_PORT`
- `BACKEND_INTERNAL_PORT`
- `FRONTEND_PORT`

Variables frontend:

- `VITE_API_URL`

## Levantar con Docker Compose

Requisitos:

- Docker.
- Docker Compose v2 recomendado: `docker compose`.
- Alternativa compatible si el entorno solo tiene Compose v1: `docker-compose`.

PowerShell:

```bash
Copy-Item .env.example .env
docker compose up --build
```

Git Bash:

```bash
cp .env.example .env
docker compose up --build
```

Si tu entorno no tiene Compose v2, usa:

```bash
docker-compose up --build
```

Servicios:

- Backend: `http://localhost:18000`
- Swagger: `http://localhost:18000/api/v1/docs`
- Health: `http://localhost:18000/health`
- Ready: `http://localhost:18000/ready`
- Frontend: `http://localhost:15173`
- Mock meeting: `http://localhost:15173/mock-meeting/{meetingId}`
- PostgreSQL: `localhost:25432`

Puertos publicados por defecto:

- `FRONTEND_PORT=15173`
- `BACKEND_PORT=18000`
- `POSTGRES_PORT=25432`

Si necesitas otros, cambia esos valores en `.env` antes de ejecutar `docker compose up --build`.

## Diagnostico rapido

```bash
docker compose ps
docker compose logs --tail=200 backend
docker compose logs --tail=200 frontend
docker compose logs --tail=200 db
curl http://localhost:18000/health
curl http://localhost:18000/ready
```

Con Compose v1:

```bash
docker-compose ps
docker-compose logs --tail=200 backend
docker-compose logs --tail=200 frontend
docker-compose logs --tail=200 db
```

Que revisar:

- si `db` no esta healthy, el backend no iniciara migraciones ni seed;
- si `backend` no esta healthy, revisa `CORS_ORIGINS`, `DATABASE_URL` y logs de bootstrap;
- si el frontend carga pero no autentica, valida `VITE_API_URL` y el estado de `backend`.
- si `docker compose` no existe, intenta `docker-compose`;
- si Docker responde `Acceso denegado` al daemon en Windows, ejecuta la terminal con permisos suficientes o revisa Docker Desktop.

Reinicio seguro sin eliminar volumenes:

```bash
docker compose restart
```

No uses `down -v` salvo que quieras borrar datos locales y tengas una instruccion explicita para hacerlo.

## Desarrollo local

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
pytest
alembic upgrade head
python -m app.seed.run
uvicorn app.main:app --reload
```

En PowerShell puedes copiar el ejemplo con:

```powershell
Copy-Item .env.example .env
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

El frontend consume el backend mediante `VITE_API_URL`. Para Docker, el valor por defecto es `http://localhost:18000`.

## Migraciones

```bash
cd backend
alembic upgrade head
```

Migracion incluida:

- `20260611_0001_initial`
- `20260714_0002_catalog_constraints`
- `20260714_0003_appointment_active_slot_constraints`

## Seed demo

Credenciales iniciales:

- Admin: `admin@realmeet.local` / `Admin123!`
- Profesional: `professional@realmeet.local` / `Professional123!`
- Cliente: `client@realmeet.local` / `Client123!`

Datos iniciales:

- Categorias: Salud, Legal
- Especialidades salud: Psicologia, Medicina General, Nutricion
- Especialidades legal: Derecho Laboral, Derecho Familiar, Derecho Civil
- Profesional demo con disponibilidad de lunes a viernes de 09:00 a 17:00

El seed es idempotente: reutiliza usuarios, categorias, especialidades, perfil profesional, relaciones y reglas de disponibilidad existentes cuando ya fueron creados. No registra passwords en logs.

## Troubleshooting

- Puerto ocupado: cambia `FRONTEND_PORT`, `BACKEND_PORT` o `POSTGRES_PORT` en `.env`.
- PostgreSQL no saludable: revisa `docker compose logs --tail=200 db`.
- Migracion fallida: revisa `docker compose logs --tail=200 backend`; el backend ejecuta `alembic upgrade head` antes de iniciar Uvicorn.
- Seed fallido: revisa logs backend; el seed hace rollback y registra `seed_failed` sin imprimir contrasenas.
- Frontend sin conexion: valida `VITE_API_URL` y `GET http://localhost:18000/ready`.
- CORS: valida `CORS_ORIGINS`; acepta JSON o CSV.
- Variables faltantes: backend falla temprano si faltan `SECRET_KEY`, `DATABASE_URL` o CORS queda vacio.
- Compose v1 vs v2: `docker compose` es recomendado; `docker-compose` funciona como alternativa cuando v2 no esta disponible.
- Staging: usa `APP_ENV=staging`, `DEBUG=false`, `ENABLE_DEMO_SEED=false`, `ENABLE_DOCS=false` si la instancia es publica, `CORS_ORIGINS` explicito y `SECRET_KEY` fuerte de 32+ caracteres.

## Seguridad implementada hasta Modulo 2

- Login rechaza usuarios inactivos.
- JWT valida firma, expiracion y `sub` numerico.
- Token ausente, invalido, vencido o asociado a usuario inactivo responde `401`.
- Usuario autenticado sin rol permitido responde `403`.
- `/auth/me` no expone password, hash ni token.
- `/users/me` usa contrato propio y no permite modificar `role` ni `is_active`.
- Perfil cliente propio: `GET/PATCH /users/me/profile`, solo para `client`.
- Perfil profesional propio: `POST /professionals/profile`, `GET/PATCH /professionals/me/profile`, solo para `professional`, sin `category_id`, `specialty_ids`, `price`, `is_public`, verificaciones ni licencia.
- Frontend limpia sesion ante `401`, restaura sesion con `/auth/me`, restringe rutas por rol y logout limpia token/usuario.
- Backend agrega headers basicos de seguridad: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y `Cache-Control: no-store` en rutas sensibles.
- Login y creacion de reservas tienen rate limiting en memoria configurable mediante `RATE_LIMIT_*`.
- Swagger/OpenAPI se controla con `ENABLE_DOCS`; no eliminar la documentacion en desarrollo.
- El seed demo se controla con `ENABLE_DEMO_SEED`; en staging publico debe estar deshabilitado y las credenciales demo deben rotarse o desactivarse.

Deuda tecnica aceptada:

- El token sigue en `localStorage`; migrar a cookies `HttpOnly`/`SameSite` queda para hardening posterior.
- El rate limiter en memoria es solo para una instancia; produccion multi-instancia requiere Redis, gateway o WAF.
- `npm audit` informa 5 vulnerabilidades: `axios` high, `react-router/react-router-dom` high, `vite` high y `postcss` moderate. No se ejecuto `npm audit fix --force` porque requiere cambios fuera de rango y fuera de alcance del modulo.

## Backup y restauracion PostgreSQL

Estos comandos son para el servicio `db` de Docker Compose y no borran volumenes. Guarda los archivos fuera del repositorio.

Crear backup:

```bash
docker-compose exec -T db pg_dump -U realmeet -d realmeet -Fc > backups/realmeet-YYYYMMDD.dump
```

Validar contenido del backup:

```bash
docker-compose exec -T db pg_restore --list < backups/realmeet-YYYYMMDD.dump
```

Restaurar en una base aislada o staging temporal:

```bash
docker-compose exec -T db createdb -U realmeet realmeet_restore_test
docker-compose exec -T db pg_restore -U realmeet -d realmeet_restore_test --clean --if-exists < backups/realmeet-YYYYMMDD.dump
```

No restaures sobre la base activa sin backup previo, ventana de mantenimiento y plan de rollback. No uses `docker-compose down -v` para probar restauraciones.

## Dependencias y licencias

Politica del proyecto:

- Solo dependencias open source compatibles con uso comercial
- Preferencia por `MIT`, `BSD-3-Clause`, `Apache-2.0` y `PostgreSQL License`
- Se evitan `GPL` y `AGPL`

Principales dependencias documentadas:

### Backend

- FastAPI - MIT
- Uvicorn - BSD-3-Clause
- SQLAlchemy - MIT
- Alembic - MIT
- pg8000 - BSD-3-Clause
- Pydantic - MIT
- pydantic-settings - MIT
- PyJWT - MIT
- passlib - BSD
- APScheduler - MIT
- python-dotenv - BSD-3-Clause
- cryptography - Apache-2.0/BSD, usado para cifrado autenticado de tokens OAuth recuperables.

### Frontend

- React - MIT
- React DOM - MIT
- Vite - MIT
- TypeScript - Apache-2.0
- Tailwind CSS - MIT
- React Router - MIT
- Axios - MIT
- TanStack Query - MIT
- Zustand - MIT

### Base de datos

- PostgreSQL - PostgreSQL License

## Contratos administrativos

`PATCH /admin/appointments/{id}/status` recibe un body con `new_status` y `reason`, usando el contrato `AppointmentStatusUpdate`. No se aceptan campos de notas privadas del profesional en contratos administrativos de reservas.

## Estado MVP integrado

El cierre del Modulo 8 consolida el MVP para desarrollo local y demo controlada: autenticacion, roles, perfiles, catalogo, disponibilidad, reservas, historial, reuniones mock, notificaciones, dashboards, metricas, backoffice minimo y auditoria administrativa basica.

Readiness:

- Desarrollo local: listo si pasan las validaciones finales documentadas en `specs/modules/module-08-mvp-closure/validation-report.md`.
- Demo: apto para demo controlada con datos no reales.
- Staging: preparado con checklist previo en `specs/modules/module-08-mvp-closure/staging-checklist.md`.
- Produccion: no listo; requiere hardening, secretos reales, HTTPS, backups, monitoreo, SAST/SCA, rate limiting y operacion.
- Uso clinico real: no listo; requiere privacidad clinica, consentimiento, retencion, auditoria regulatoria y cumplimiento legal.

Modulo 9 agrega hardening tecnico para staging: settings por entorno, rechazo de secretos inseguros en staging/production, headers HTTP, rate limiting basico, Swagger configurable, seed demo configurable, Docker no root cuando es viable y documentacion de backup/restauracion.
## Preparacion productiva

El MVP funcional completo queda cerrado en `staging`, pero no se declara listo para produccion real. La fase de robustecimiento queda documentada en:

- `docs/hardening/technical-debt-register.md`
- `docs/hardening/environment-readiness-gates.md`
- `docs/hardening/production-readiness-roadmap.md`
- `docs/hardening/mvp-risk-register.md`
- `specs/hardening/production-readiness-plan/spec.md`

Estos documentos consolidan deuda tecnica, gates por ambiente, roadmap H0-H7, riesgos del MVP y estrategia futura de CI/CD/testing. No reemplazan la implementacion de hardening ni habilitan despliegue productivo por si mismos.

## Integraciones Google OAuth y Meet

El Modulo 12.1 prepara autorizacion OAuth administrativa para una integracion `google_meet`.

El Modulo 12.2 agrega un proveedor Google Meet controlado desde backoffice admin para pruebas manuales: crea eventos de Google Calendar con `conferenceDataVersion=1`, solicita conferencia `hangoutsMeet`, persiste referencias reducidas en RealMeet y permite consultar/cancelar reuniones conocidas. Este flujo no se conecta todavia a las reservas; las reservas siguen usando el provider mock hasta el submodulo 12.3.

El Modulo 12.3 conecta la provision de reuniones con reservas confirmadas mediante una politica operativa configurada en la integracion `google_meet`. Google Meet puede integrarse con nuevas reservas segun la politica configurada. No existen reintentos automaticos ni sincronizacion bidireccional en este submodulo.

Politicas disponibles:

- `mock_only`: crea siempre una reunion mock.
- `google_preferred`: intenta Google Meet y usa mock como fallback controlado.
- `google_required`: exige Google Meet; si falla, la reserva permanece y la reunion queda pendiente de resolucion administrativa.
- `disabled`: no crea reunion automatica.

Variables:

- `GOOGLE_OAUTH_CLIENT_ID`: client ID de Google Cloud. Debe quedar vacio en Git.
- `GOOGLE_OAUTH_CLIENT_SECRET`: client secret de Google Cloud. Debe quedar vacio en Git.
- `GOOGLE_OAUTH_REDIRECT_URI`: callback backend, por defecto local `http://localhost:18000/api/v1/admin/integrations/oauth/google/callback`.
- `GOOGLE_OAUTH_SCOPES`: scope minimo `https://www.googleapis.com/auth/calendar.events`.
- `GOOGLE_OAUTH_STATE_TTL_SECONDS`: TTL del state firmado.
- `GOOGLE_TOKEN_ENCRYPTION_KEY`: clave Fernet generada fuera del repositorio.

Para crear credenciales en Google Cloud, configura una aplicacion OAuth web, registra el redirect URI exacto y solicita solo el scope de eventos de calendario. No agregues Gmail, Drive, contactos ni scopes amplios. Los tokens de la cuenta autorizada se guardan cifrados en base de datos y nunca se muestran en API ni frontend.

Notas operativas:

- La creacion real de reuniones requiere una integracion `google_meet` habilitada y una credencial OAuth activa.
- La operacion admin usa idempotency key para evitar crear dos eventos por doble ejecucion.
- `sendUpdates` queda en `none` por defecto; otros modos deben elegirse de forma explicita.
- No ingreses tokens, client secrets ni credenciales reales en el formulario de integraciones.
- La cancelacion de reserva intenta cancelar la reunion externa, pero nunca revierte la cancelacion de la reserva si Google falla.
- Los administradores pueden reintentar creacion, reintentar cancelacion y reconciliar manualmente desde el backoffice de reservas.

## WhatsApp Cloud

El Modulo 13.1A prepara la base backend para WhatsApp Cloud API: configuracion local, referencias de secretos, normalizacion telefonica, HMAC privado, consentimiento explicito y plantillas locales. El Modulo 13.1B agrega recepcion segura de webhooks.

El Modulo 13.2 agrega un proveedor WhatsApp Cloud controlado para envio administrativo explicito de mensajes de plantilla. El Modulo 13.3 conecta WhatsApp con reservas confirmadas, canceladas, recordatorios y enlace de reunion disponible mediante una politica administrativa, consentimiento activo, plantillas aprobadas, idempotencia y fallback a email.

RealMeet puede generar notificaciones transaccionales de WhatsApp para nuevas reservas segun consentimiento y politica. Los mensajes se construyen desde datos actuales de la reserva y no se almacena su contenido renderizado.

Arquitectura actual:

- `Integration` usa `integration_type=messaging` y `provider=whatsapp_cloud`.
- La configuracion no secreta vive en `Integration.config` y valida WABA ID, Phone Number ID, Graph API version, idioma, pais y telefono visible enmascarado.
- Las credenciales reales permanecen fuera de la base como variables de entorno; la integracion guarda solo referencias tipo `WHATSAPP_ACCESS_TOKEN`.
- `WhatsAppConsent` registra consentimiento por usuario, telefono normalizado, finalidad y estado, con telefono enmascarado para salida administrativa.
- `WhatsAppTemplate` registra definiciones locales de plantillas `utility`; la sincronizacion admin de 13.2 actualiza estado, idioma e ID remoto desde Meta sin crear, editar ni borrar plantillas remotas.
- `WhatsAppMessage` registra mensajes salientes reducidos, con destinatario enmascarado, estado, idempotencia, ID externo parcial en respuestas y timestamps. No almacena telefono completo, variables completas, contenido renderizado, request, response ni token.
- `WhatsAppWebhookEvent` registra eventos entrantes reducidos, deduplicados y sin payload completo.
- `WhatsAppCloudClient` construye requests HTTP hacia `https://graph.facebook.com/{graph_api_version}/{phone_number_id}/messages` usando solo configuracion validada del backend.
- `WhatsAppMessagingService` valida integracion habilitada, token de entorno, consentimiento activo, plantilla `utility` aprobada, variables permitidas e idempotencia antes de invocar al cliente.
- `AppointmentNotification` registra trazabilidad reducida por reserva, evento y canal; puede vincularse a `WhatsAppMessage` y no almacena contenido renderizado ni variables.
- La politica transaccional vive en `Integration.config`: `email_only`, `whatsapp_preferred`, `whatsapp_required`, `email_and_whatsapp` o `notifications_disabled`, con fallback fijo a email y recordatorio inicial configurable.
- No existe conexion con mensajes libres, respuestas, workers, colas externas, marketing ni bulk messages.

Variables WhatsApp:

- `WHATSAPP_CLOUD_ENABLED`: bandera local de preparacion, por defecto `false`.
- `WHATSAPP_GRAPH_API_VERSION`: version Graph API configurable, sin valor real por defecto.
- `WHATSAPP_ACCESS_TOKEN`: token real solo en entorno seguro, nunca en Git.
- `WHATSAPP_APP_SECRET`: app secret real solo en entorno seguro, nunca en Git.
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`: verify token futuro, nunca en Git.
- `WHATSAPP_DEFAULT_LANGUAGE`: idioma por defecto, por ejemplo `es_CL`.
- `WHATSAPP_DEFAULT_COUNTRY_CODE`: pais por defecto para normalizacion, por ejemplo `CL`.
- `WHATSAPP_PHONE_HMAC_KEY`: clave HMAC fuera de Git para correlacion privada de telefonos.
- `WHATSAPP_WEBHOOK_PUBLIC_URL`: URL publica informativa para configurar Meta.
- `WHATSAPP_WEBHOOK_MAX_BODY_BYTES`: limite de body, por defecto `262144`.
- `WHATSAPP_WEBHOOK_EVENT_RETENTION_DAYS`: retencion futura documentada, por defecto `30`.
- `WHATSAPP_WEBHOOK_REQUIRE_SIGNATURE`: exige `X-Hub-Signature-256`, por defecto `true`.
- `WHATSAPP_HTTP_CONNECT_TIMEOUT_SECONDS`: timeout de conexion para Graph API, por defecto `3`.
- `WHATSAPP_HTTP_READ_TIMEOUT_SECONDS`: timeout de lectura para Graph API, por defecto `8`.
- `WHATSAPP_HTTP_TOTAL_TIMEOUT_SECONDS`: timeout total para Graph API, por defecto `10`.

APIs backend disponibles:

- Usuario autenticado: `GET/POST /api/v1/users/me/whatsapp-consents` y `DELETE /api/v1/users/me/whatsapp-consents/{purpose}`.
- Admin: estado/validacion local bajo `/api/v1/admin/integrations/{integration_id}/whatsapp`.
- Admin: plantillas locales bajo `/api/v1/admin/integrations/{integration_id}/whatsapp/templates`.
- Admin: sincronizacion read-only de plantillas con Meta en `POST /api/v1/admin/integrations/{integration_id}/whatsapp/templates/sync`.
- Admin: health check read-only en `POST /api/v1/admin/integrations/{integration_id}/whatsapp/health-check`.
- Admin: mensajes salientes en `GET/POST /api/v1/admin/integrations/{integration_id}/whatsapp/messages` y retry manual en `/messages/{message_id}/retry`.
- Admin: politica transaccional en `GET/PATCH /api/v1/admin/integrations/{integration_id}/whatsapp/notification-policy`.
- Admin: trazabilidad de reservas en `GET /api/v1/admin/appointment-notifications`, detalle, retry, reconcile y cancelacion pendiente.
- Admin: resumen seguro y correcciones auditadas bajo `/api/v1/admin/whatsapp/consents`.
- Webhook publico: `GET/POST /api/v1/integrations/whatsapp/webhook`.
- Admin: eventos webhook bajo `/api/v1/admin/integrations/{integration_id}/whatsapp/webhook-events` y estado bajo `/webhook-status`.

Webhooks:

- GET verifica `hub.mode`, `hub.verify_token` y devuelve `hub.challenge` como texto plano si coincide.
- POST usa el body crudo para validar `X-Hub-Signature-256: sha256=<digest>` con HMAC-SHA256.
- El body se limita por configuracion y no se persiste.
- Se clasifican eventos `inbound_message`, `message_sent`, `message_delivered`, `message_read`, `message_failed`, `template_status` y `unknown`.
- La idempotencia usa `event_key` unico; reintentos incrementan `received_count` y no crean segunda fila.
- Los status webhooks correlacionan `external_message_id` con `WhatsAppMessage` y actualizan estado de forma monotona: `accepted -> sent -> delivered -> read`; estados desconocidos no crean mensajes ficticios.
- El rate limiting especifico de webhooks queda diferido hasta definir proxy/IP confiable; las protecciones actuales son firma, tamano e idempotencia.
- La limpieza automatica por retencion queda diferida; no se usa APScheduler para webhooks en esta etapa.

Seguridad:

- No pegues tokens, app secrets, verify tokens ni credenciales en `Integration.config`.
- Los listados administrativos no exponen telefono completo ni hash.
- Los eventos webhook no almacenan body, texto de mensajes, headers, firmas, contactos ni telefonos completos.
- Las finalidades iniciales son transaccionales: `appointment_transactional`, `appointment_reminders` y `appointment_updates`.
- El envio real exige consentimiento activo y plantilla local `utility` aprobada. No se acepta telefono libre, token, Graph URL, headers ni Phone Number ID desde frontend.
- La idempotencia de envio usa `(integration_id, idempotency_key)`. Un mensaje aceptado no se reenvia con la misma clave; un fallo puede reintentarse manualmente.
- La idempotencia de reservas usa claves deterministicas por reserva, evento, version y canal. Un timeout ambiguo de WhatsApp queda como entrega incierta y no dispara fallback inmediato.
- El token se resuelve desde la referencia de entorno y permanece solo en memoria durante la llamada.
- Marketing, campanas, mensajes libres, bots y WhatsApp Flows quedan fuera de esta etapa.

## Webhooks salientes operativos

RealMeet puede emitir eventos operativos mediante webhooks firmados.

Modulo 14.1 agrega:

- Catalogo inicial de eventos: `appointment.created`, `appointment.updated`, `appointment.cancelled`, `appointment.confirmed`, `meeting.ready`, `notification.sent`, `notification.failed`, `client.created`, `professional.created` y `webhook.test`.
- Suscripciones administrativas vinculadas a integraciones `generic_webhook` o `n8n`.
- Entregas persistidas con idempotencia por suscripcion y evento.
- Firma HMAC-SHA256 con `X-RealMeet-Signature`.
- Headers `X-RealMeet-Event`, `X-RealMeet-Delivery` y `X-RealMeet-Timestamp`.
- Cliente HTTP saliente con timeout breve y sin redirects.
- Proveedor fake para pruebas automatizadas.
- Reintento manual de entregas fallidas.

Los eventos conectados inicialmente son `appointment.created` y `appointment.cancelled`. El payload incluye solo IDs y datos operativos minimos de la reserva; no incluye telefonos, emails, notas privadas, datos clinicos, meeting URL, secretos ni modelos completos.

APIs admin disponibles:

- `GET/POST /api/v1/admin/webhook-subscriptions`
- `GET/PATCH /api/v1/admin/webhook-subscriptions/{id}`
- `POST /api/v1/admin/webhook-subscriptions/{id}/enable`
- `POST /api/v1/admin/webhook-subscriptions/{id}/disable`
- `POST /api/v1/admin/webhook-subscriptions/{id}/test`
- `GET /api/v1/admin/webhook-deliveries`
- `POST /api/v1/admin/webhook-deliveries/{id}/retry`

Seguridad:

- La URL debe ser HTTPS, salvo `localhost` en entornos locales.
- No se permiten credenciales embebidas en la URL.
- IPs privadas y localhost quedan bloqueados fuera de entornos locales.
- El secreto se guarda solo como referencia de variable de entorno y se resuelve en memoria.
- No se persiste el body completo de respuesta.

Modulo 14.2 agrega soporte especifico para n8n sobre esta misma base. RealMeet puede activar workflows de n8n mediante eventos firmados. Los workflows se configuran y ejecutan fuera de RealMeet.

- Las integraciones n8n usan `integration_type=automation` y `provider=n8n`.
- La configuracion no secreta guarda `base_url` y `environment`; cada workflow define un `webhook_path` relativo.
- Cada workflow n8n se respalda internamente con una `WebhookSubscription`, por lo que reutiliza firma, idempotencia, timeout, cliente HTTP y `WebhookDelivery`.
- Eventos disponibles para workflow: `appointment.created`, `appointment.cancelled`, `meeting.ready` y `notification.failed`; en esta etapa las reservas publican `appointment.created` y `appointment.cancelled`.
- El test manual usa `n8n.workflow.test`.
- La UI administrativa permite crear la integracion n8n, registrar workflows, habilitarlos, deshabilitarlos, probarlos y revisar entregas recientes.

APIs admin n8n:

- `GET/POST /api/v1/admin/integrations/{id}/n8n/workflows`
- `GET/PATCH /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/enable`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/disable`
- `POST /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/test`
- `GET /api/v1/admin/integrations/{id}/n8n/workflows/{workflow_id}/deliveries`

n8n no administra credenciales, no importa/exporta workflows, no ejecuta llamadas inbound hacia RealMeet y no implementa colas ni retries automaticos en 14.2.

Modulo 14.3 agrega contratos de payload operativos y ejemplos importables para n8n en `docs/n8n/examples/`. El backoffice lista ejemplos para Google Sheets, CRM generico y notificacion interna, y los endpoints admin permiten obtener el JSON catalogado sin exponer rutas internas. RealMeet no se conecta directamente a Google Sheets, CRM o Slack; solo emite eventos firmados hacia workflows configurados fuera de RealMeet.

## Pagos y ordenes de cobro

Modulo 17.1 agrega una fundacion provider-agnostic de pagos:

- `PaymentOrder` como intencion interna de cobro.
- `PaymentOrderStatusHistory` para historial de transiciones.
- Estados: `draft`, `pending`, `requires_action`, `approved`, `rejected`, `cancelled`, `expired`, `failed` y `refunded`.
- Moneda inicial unica: `CLP`; se rechazan montos cero, negativos o fraccionarios.
- Provider `fake` implementado para pruebas deterministicas.
- Registry con `fake`, `mercado_pago` y `stripe`; los dos ultimos responden como no implementados en 17.1.
- Idempotencia en creacion mediante `Idempotency-Key` y fingerprint de payload.
- Maximo una orden activa o aprobada por reserva.
- Respuestas publicas de cliente/profesional sin fingerprint, idempotency key, referencias internas ni datos de provider sensibles.

No existe una tabla de servicios independiente en el catalogo actual. Cuando una orden se asocia a una reserva, RealMeet toma snapshot del precio del perfil profesional. Si no hay reserva o precio disponible, el backoffice puede indicar un monto manual en 17.1.

Modulo 17.2 agrega checkout fake autenticado y politicas de reserva basadas en pago. La politica se almacena en `ProfessionalProfile` como servicio actual del catalogo para no crear una entidad nueva antes de que exista un CRUD de servicios dedicado.

Politicas disponibles:

- `no_payment`: comportamiento anterior; no crea orden automatica ni checkout.
- `pay_before_confirmation`: crea reserva `pending_payment`, genera una orden fake y confirma solo cuando el pago queda `approved`.
- `pay_after_confirmation`: confirma inmediatamente, crea una orden pendiente y no cancela automaticamente si el pago se rechaza.

Campos administrativos de politica:

- `payment_timing`
- `payment_amount`
- `payment_currency`, limitado a `CLP`
- `payment_expiration_minutes`, rango `5` a `1440`, default `30`
- `allow_manual_confirmation`

La reserva `pending_payment` bloquea el slot mientras espera pago. Si el pago se rechaza o expira, la reserva pasa a `cancelled` y deja de bloquear disponibilidad. Una reserva cancelada por rechazo o expiracion no se reactiva automaticamente, porque el horario pudo haber sido tomado por otra persona; el cliente debe consultar disponibilidad y crear una nueva reserva.

Modulo 17.3 agrega Mercado Pago Checkout Pro como primer provider real:

- Configuracion via `Integration` con `integration_type=payment` y `provider=mercado_pago`.
- Credenciales solo por referencias de entorno: `access_token_reference` y `webhook_secret_reference`.
- Creacion de preferencia Checkout Pro con `X-Idempotency-Key` estable.
- Persistencia minima: preference ID, checkout URL, estado provider y ultimo sync.
- Webhook publico firmado en `/api/v1/webhooks/mercado-pago`, deduplicado y verificado consultando la API del provider.
- `sync-provider` administrativo para consulta manual.
- Retornos frontend informativos en `/payments/success`, `/payments/pending` y `/payments/failure`.

RealMeet no procesa tarjetas, no guarda access tokens y no aprueba pagos solo por retorno del navegador.

APIs principales:

- `GET/POST /api/v1/admin/payment-orders`
- `GET /api/v1/admin/payment-orders/{payment_order_id}`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/submit`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/cancel`
- `GET /api/v1/admin/payment-orders/{payment_order_id}/history`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/fake/approve`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/fake/reject`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/fake/expire`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/fake/fail`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/reconcile`
- `POST /api/v1/admin/payment-orders/{payment_order_id}/sync-provider`
- `POST /api/v1/admin/payment-providers/{provider}/health`
- `GET /api/v1/professionals/me/payment-orders`
- `GET /api/v1/professionals/me/payment-orders/{payment_order_id}`
- `GET /api/v1/clients/me/payment-orders`
- `GET /api/v1/clients/me/payment-orders/{payment_order_id}`
- `GET /api/v1/clients/me/payment-orders/{payment_order_id}/checkout`
- `POST /api/v1/clients/me/payment-orders/{payment_order_id}/checkout/approve`
- `POST /api/v1/clients/me/payment-orders/{payment_order_id}/checkout/reject`
- `POST /api/v1/webhooks/mercado-pago`

17.3 no implementa checkout publico anonimo, tarjetas dentro de RealMeet, produccion real automatica, reembolsos, impuestos, descuentos, facturacion, suscripciones, scheduler de expiracion, retries automaticos ni conciliacion bancaria.

## Plan sugerido de commits

El repositorio tiene commits incrementales por modulo. El Modulo 8 debe cerrarse con un unico commit y sin push salvo instruccion explicita.

## Limitaciones actuales del MVP

- Integracion automatica de reservas con Google Meet y Zoom no implementada.
- WhatsApp permite envio manual administrativo y notificaciones transaccionales de reservas con consentimiento; mensajes libres, respuestas y campanas quedan diferidos. Pagos tiene fundacion interna, checkout fake y Mercado Pago Checkout Pro preparado para sandbox; produccion real, suscripciones y facturacion quedan diferidos.
- Recuperacion de contrasena, MFA y roles configurables quedan diferidos.
- Pruebas frontend automaticas y E2E completas quedan diferidas.
- El backoffice es minimo y prioriza operacion inicial sobre cobertura total de UX.
- Reprogramacion, recordatorios avanzados y correos transaccionales completos quedan fuera del MVP.
- Produccion y uso clinico real requieren hardening y cumplimiento adicional.
