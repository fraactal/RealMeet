# Submodulo 11.1 - Dominio y persistencia de integraciones

## Problema

RealMeet ya tiene reservas, reuniones mock y notificaciones, pero no cuenta con una base generica para administrar futuras integraciones externas sin acoplar proveedores a reservas, routers o componentes visuales.

## Objetivo

Definir el dominio persistente minimo para integraciones: tipos, proveedores conocidos, estados, configuracion no secreta, referencias seguras a secretos, ejecuciones operativas e idempotencia basica.

## Alcance

- Enums estables para tipos, proveedores, estado de configuracion/salud y estado de ejecucion.
- Modelo `Integration`.
- Modelo `IntegrationExecution`.
- Schemas Pydantic explicitos para creacion, actualizacion y lectura.
- Repositorios acotados de integraciones y ejecuciones.
- Validacion recursiva de configuracion y metadata contra claves sensibles.
- Validacion de `secret_reference` con formato de variable de entorno.
- Migracion Alembic reversible.
- Pruebas minimas de schema, seguridad y persistencia.

## Fuera de alcance

- API administrativa.
- Servicio de ejecucion.
- Registro de proveedores.
- Proveedor mock ejecutable.
- Backoffice frontend.
- Navegacion.
- Google Meet, WhatsApp, n8n, calendarios o cualquier proveedor real.
- Cambios a reservas, reuniones existentes, emails o seed.

## Entidades

### Integration

Configuracion administrativa de una integracion futura. Guarda nombre, categoria, proveedor, habilitacion, estado operativo/configuracion, configuracion no secreta y referencia opcional a secretos.

### IntegrationExecution

Registro operativo de un intento futuro de ejecucion. Guarda operacion, entidad relacionada opcional, clave idempotente, estado, intento, metadata segura, errores resumidos y tiempos.

## Enums

- `IntegrationType`: `meeting`, `calendar`, `messaging`, `email`, `automation`, `webhook`.
- `IntegrationProvider`: `mock`, `google_meet`, `google_calendar`, `microsoft_365`, `whatsapp_cloud`, `twilio`, `smtp`, `n8n`, `generic_webhook`.
- `IntegrationStatus`: `not_configured`, `configured`, `healthy`, `error`, `unsupported`.
- `IntegrationExecutionStatus`: `pending`, `running`, `succeeded`, `failed`, `skipped`.

## Decision de estados

`enabled` queda como booleano independiente y comienza en `false`. `status` representa configuracion/salud, no habilitacion. Asi se evita duplicar estados contradictorios como `enabled` y `disabled` dentro del enum.

## Restricciones

- `Integration.name` obligatorio, maximo 120 caracteres.
- `integration_type` y `provider` obligatorios.
- `enabled` por defecto `false`.
- `status` por defecto `not_configured`.
- `config` por defecto `{}`.
- `secret_reference` opcional con formato `^[A-Z][A-Z0-9_]{2,127}$`.
- `IntegrationExecution.operation` e `idempotency_key` obligatorios.
- `IntegrationExecution.attempt` por defecto `1`.
- `UNIQUE (integration_id, idempotency_key)`.

## Estrategia de secretos

La base de datos nunca almacena valores secretos. `config`, `request_metadata` y `response_metadata` rechazan claves sensibles de forma recursiva, insensible a mayusculas y tolerante a guiones/guiones bajos. `secret_reference` solo guarda el nombre de una variable o referencia segura, no su valor.

## Estrategia de idempotencia

La idempotencia se limita por integracion mediante `UNIQUE (integration_id, idempotency_key)`. Esto permite que proveedores distintos reutilicen claves semanticas futuras, por ejemplo `appointment:123:meeting:create`, sin bloquear operaciones equivalentes de otra integracion.

## Seguridad

- Schemas con `extra="forbid"` para prevenir mass assignment.
- Campos operacionales protegidos fuera de payloads de creacion/actualizacion.
- Metadata minimizada y validada.
- Longitudes maximas razonables.
- Sin variables nuevas de proveedor ni cambios en `.env.example`.
- Sin seed automatico de integraciones.

## Riesgos

- La validacion de secretos por clave no detecta valores sensibles si la clave parece inocua.
- La proteccion SSRF completa se implementara cuando existan webhooks o llamadas reales.
- La semantica final de proveedores soportados se completara en 11.2 con registro y servicio.

## Validacion minima

- Alembic upgrade head.
- Pruebas acotadas de schemas, validacion recursiva, persistencia, uniqueness e idempotencia.
- Alembic current.
- Health y readiness.

## Relacion con 11.2, 11.3 y 11.4

- 11.2 usara estos modelos para servicios, registro de proveedores, mock ejecutable y API admin.
- 11.3 usara la API para backoffice y navegacion administrativa.
- 11.4 cerrara validacion integrada, seguridad y documentacion final del modulo.
