# Estado de implementacion 10.7

Estado: Completado

## Correcciones aplicadas

- `PublicHeader` ahora cierra el menu mobile con Escape.
- `PublicHeader` bloquea el scroll de fondo mientras el menu mobile esta abierto.
- `AppShell` bloquea el scroll de fondo mientras el drawer autenticado mobile esta abierto.
- El overlay de `MobileNavigation` declara `type="button"`.
- Se elimino `frontend/src/components/Navbar.tsx`, componente publico anterior sin imports.

## Sin cambios

- No se modifico backend.
- No se cambiaron guards, permisos, roles ni contratos API.
- No se agregaron dependencias.
- No se inicio Modulo 11.
