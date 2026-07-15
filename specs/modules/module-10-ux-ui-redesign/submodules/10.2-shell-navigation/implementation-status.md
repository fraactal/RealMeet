# Estado de implementacion - 10.2

## Implementado

- Configuracion central de navegacion en `frontend/src/config/navigation.ts`.
- Shell autenticado reutilizable con `AppShell`.
- Sidebar desktop por rol.
- Header superior con contexto, usuario, rol traducido, avatar y logout.
- Drawer mobile con overlay, cierre por boton, cierre al navegar y cierre con Escape.
- Refactor de `DashboardLayout` para delegar en `AppShell`.
- Capturas representativas por rol.

## Restricciones

- No modificar backend.
- No modificar contratos de API.
- No cambiar guards de autenticacion/autorizacion.
- No avanzar a experiencia profesional 10.3.

## Notas

- Los contenidos internos de dashboards mantienen textos y estructura previos. Su rediseño corresponde a 10.3, 10.4 y 10.5.
- La ruta publica `/professionals` se conserva para clientes como ruta real existente; no se creo una pagina ficticia.
