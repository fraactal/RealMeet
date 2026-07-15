# Submodulo 11.3 - Backoffice de integraciones

## Objetivo

Crear la interfaz administrativa para gestionar integraciones usando exclusivamente la API backend de 11.2.

## Alcance

- Ruta protegida `/dashboard/admin/integrations`.
- Entrada de navegacion admin `Integraciones`.
- Pagina `AdminIntegrationsPage`.
- API frontend tipada para integraciones.
- Tipos TypeScript para integraciones, ejecuciones y resultados.
- Traducciones centralizadas de tipos, proveedores y estados.
- Formulario de creacion/edicion.
- Acciones de validar, habilitar, deshabilitar, health check y prueba mock.
- Listado de ejecuciones recientes.
- Responsive desktop/mobile.

## Fuera de alcance

- Cambios funcionales backend.
- Nuevas migraciones.
- Proveedores externos reales.
- Backoffice avanzado por proveedor.
- Eliminacion de integraciones.
- 11.4, Modulo 12, push, merge o despliegue.

## Ruta frontend

- `/dashboard/admin/integrations`

La ruta usa `RequireAuth allowedRoles={["admin"]}` dentro del shell existente.

## Endpoints usados

- `GET /admin/integrations`
- `POST /admin/integrations`
- `PATCH /admin/integrations/{id}`
- `POST /admin/integrations/{id}/validate`
- `POST /admin/integrations/{id}/enable`
- `POST /admin/integrations/{id}/disable`
- `POST /admin/integrations/{id}/health-check`
- `POST /admin/integrations/{id}/test`
- `GET /admin/integrations/{id}/executions`

## Estados de UI

- Loading, error y vacio global.
- Loading por mutacion.
- Resultado operativo normalizado.
- Lista de ejecuciones vacia.
- Proveedor futuro deshabilitado en formulario.

## Componentes

La pagina concentra componentes internos pequenos para evitar fragmentacion prematura:

- badges de estado;
- cards/filas de integracion;
- formulario modal;
- panel de resultado;
- listado de ejecuciones.

## Autorizacion

La navegacion admin solo muestra `Integraciones` para rol admin. La ruta directa queda protegida por `RequireAuth`. Backend sigue aplicando `require_admin`.

## Traducciones

Se agregan helpers en `utils/labels.ts` para tipos, proveedores, estados de integracion y estados de ejecucion.

## Responsive

Desktop usa tabla para listado. Mobile usa cards apiladas. Formularios y acciones pasan a una columna cuando el ancho es reducido.

## Riesgos

- La UI aun no contiene formularios especificos para proveedores futuros.
- La pagina conserva una integracion mock local para revision visual.
- No hay pruebas frontend automatizadas porque el proyecto no tiene infraestructura dedicada.

## Criterios de aceptacion

Definidos en `acceptance-criteria.md`.

## Validacion

Build frontend, pruebas backend breves, health/ready, validacion manual por rol, flujo admin y capturas.

## Deuda para 11.4

- Validacion integrada final del modulo.
- Revisión de consistencia visual completa.
- Confirmar limpieza o permanencia de datos mock segun feedback.
