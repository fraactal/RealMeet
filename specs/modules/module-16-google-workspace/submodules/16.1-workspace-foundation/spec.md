# Submodulo 16.1 - Fundacion Google Workspace y permisos incrementales

## Alcance

Implementa la fundacion Google Workspace:

- definiciones de servicios Calendar, Meet, Sheets, Drive y Docs;
- scopes incrementales centralizados;
- persistencia de habilitacion y autorizacion por servicio;
- endpoints administrativos;
- panel admin en integraciones;
- health checks seguros;
- pruebas acotadas.

## Fuera de alcance

No implementa:

- operaciones reales de Sheets;
- generacion de Docs;
- gestion de archivos Drive;
- Google Workspace Add-ons;
- service accounts;
- domain-wide delegation;
- Microsoft 365;
- workers o sincronizacion automatica;
- push, deploy, merge o tags.

## Endpoints

- `GET /api/v1/admin/integrations/{id}/google/workspace`
- `PATCH /api/v1/admin/integrations/{id}/google/workspace`
- `POST /api/v1/admin/integrations/{id}/google/workspace/oauth/start`
- `POST /api/v1/admin/integrations/{id}/google/workspace/health`
- `POST /api/v1/admin/integrations/{id}/google/workspace/services/{service}/enable`
- `POST /api/v1/admin/integrations/{id}/google/workspace/services/{service}/disable`
- `POST /api/v1/admin/integrations/{id}/google/workspace/services/{service}/health`

## Persistencia

Migracion `20260717_0017_google_workspace_foundation`:

- agrega `IntegrationOAuthState.requested_services`;
- crea `google_workspace_settings`.

## Validacion esperada

- Backend tests: `tests/test_google_workspace_foundation.py`.
- Frontend build: `docker compose exec -T frontend npm run build`.
- Alembic en head.
- `/health` y `/ready` operativos.

## Estado

Completado para revision. No se inicio 16.2.
