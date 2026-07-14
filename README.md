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
- `GET /professional/metrics`
- `GET /admin/metrics`
- `GET /admin/users`
- `GET /admin/users/{id}`
- `PATCH /admin/users/{id}`
- `GET /admin/professionals`
- `PATCH /admin/professionals/{id}`
- `GET /admin/appointments`
- `GET /admin/appointments/{id}`
- `PATCH /admin/appointments/{id}/status?new_status=confirmed`

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

Deuda tecnica aceptada:

- El token sigue en `localStorage`; migrar a cookies `HttpOnly`/`SameSite` queda para hardening posterior.
- `npm audit` informa 5 vulnerabilidades: `axios` high, `react-router/react-router-dom` high, `vite` high y `postcss` moderate. No se ejecuto `npm audit fix --force` porque requiere cambios fuera de rango y fuera de alcance del modulo.

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

## Plan sugerido de commits

El repositorio ya tiene commits incrementales hasta Modulo 2. No hacer push sin instruccion explicita.

## Limitaciones actuales del MVP

- Integraciones reales con Google Meet y Zoom no implementadas
- Frontend base funcional, pero todavia sin formularios completos de CRUD
- Pruebas automatizadas actuales son minimas y enfocadas en configuracion, health y seguridad auth/perfiles
- El backoffice es minimo y prioriza operacion inicial sobre cobertura total de UX
- El flujo de reservas basicas ya esta habilitado; reprogramacion, recordatorios y correos avanzados quedan fuera del Modulo 5.
