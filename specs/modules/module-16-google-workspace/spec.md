# Modulo 16 - Google Workspace

## Objetivo

Preparar una base segura y reutilizable para integraciones Google Workspace sobre la autorizacion Google ya existente en RealMeet.

El modulo inicia con permisos incrementales para Calendar, Meet, Sheets, Drive y Docs, sin implementar todavia flujos operativos avanzados como exportaciones, documentos, sincronizacion bidireccional o nuevas automatizaciones.

## Arquitectura

- Reutiliza `Integration`, `IntegrationCredential` e `IntegrationOAuthState`.
- Mantiene un unico OAuth Google administrativo/global.
- Agrega `GoogleWorkspaceSettings` para habilitacion local, autorizacion por servicio y ultimo estado seguro.
- Centraliza definiciones de servicios y scopes en `app.integrations.google_workspace.scopes`.
- Expone endpoints administrativos bajo `/api/v1/admin/integrations/{id}/google/workspace`.
- El frontend consume la API desde `frontend/src/api/queries.ts` y muestra el panel en el backoffice de integraciones.

## Servicios

- Calendar: usa `calendar.events`, compatible con reservas, Google Meet y calendarios externos.
- Meet: reutiliza eventos Calendar para enlaces Meet.
- Sheets: base autorizable con `spreadsheets`, sin operaciones de negocio en 16.1.
- Drive: usa `drive.file`; no solicita acceso completo a Drive.
- Docs: base autorizable con `documents`, sin generacion documental en 16.1.

## OAuth y permisos incrementales

El flujo incremental combina scopes ya concedidos con los solicitados por el servicio seleccionado y usa `include_granted_scopes=true`. No crea un segundo OAuth ni una segunda tabla de tokens.

Los tokens siguen cifrados mediante la infraestructura existente y no se retornan por API.

## Seguridad

- Los endpoints son solo admin.
- Cliente y profesional quedan bloqueados por el guard existente.
- No se exponen access tokens, refresh tokens ni codigos OAuth.
- No se agregan secretos a `.env`.
- Drive usa scope limitado `drive.file`.
- Los errores se normalizan en codigos seguros.

## Frontend

El backoffice de integraciones muestra un panel Google Workspace para integraciones `google_meet`:

- estado de cuenta;
- servicios disponibles;
- habilitacion local por servicio;
- autorizacion incremental;
- health check general y por servicio;
- scopes requeridos.

## Estado final de 16.1

Base tecnica lista para que submodulos posteriores implementen operaciones concretas sobre Sheets, Drive y Docs sin ampliar privilegios por defecto.

## Limitaciones

- OAuth Google sigue siendo administrativo/global.
- Sheets y Docs solo validan autorizacion; no prueban recursos reales.
- Drive hace un chequeo liviano con `drive.file`.
- No hay Microsoft 365, workers, sync bidireccional, watchers ni polling.

## Deuda para 16.2

- Definir el primer caso operativo Workspace sobre esta base.
- Mantener permisos incrementales por flujo.
- Agregar pruebas de negocio solo cuando exista una operacion concreta.
