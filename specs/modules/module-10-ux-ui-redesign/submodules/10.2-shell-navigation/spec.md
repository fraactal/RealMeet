# Submodulo 10.2 - Shell y navegacion

## Objetivo

Rediseñar el shell autenticado de RealMeet para que la aplicacion se perciba como un SaaS profesional, claro y consistente, manteniendo intactas las rutas, permisos y contratos existentes.

## Alcance

- Shell autenticado comun.
- Sidebar desktop.
- Header superior.
- Navegacion mobile tipo drawer.
- Metadata central de navegacion.
- Identidad del usuario con nombre, email, rol traducido y avatar por iniciales.
- Logout integrado visualmente.
- Estado activo por ruta.
- Documentacion SDD del submodulo.

## Fuera de alcance

- Rediseño profundo de dashboards.
- Rediseño de contenidos internos por rol.
- Landing y catalogo publico.
- Cambios backend.
- Cambios de API o base de datos.
- Cambios de guards o permisos.
- Nuevas funcionalidades como notificaciones, buscador global o dark mode.

## Criterios de aceptacion

| ID | Criterio | Estado |
| --- | --- | --- |
| M10.2-AC-001 | Existe un shell autenticado reutilizable. | Cumplido |
| M10.2-AC-002 | Sidebar desktop usa tokens de 10.1 e iconografia interna. | Cumplido |
| M10.2-AC-003 | Header muestra contexto, usuario, rol traducido y logout. | Cumplido |
| M10.2-AC-004 | Mobile incluye boton, drawer, overlay, cierre al navegar y Escape. | Cumplido |
| M10.2-AC-005 | La navegacion se filtra por rol sin exponer rutas no autorizadas. | Cumplido |
| M10.2-AC-006 | La ruta activa funciona en rutas hijas existentes. | Cumplido |
| M10.2-AC-007 | Guards y permisos existentes permanecen intactos. | Cumplido |
| M10.2-AC-008 | `/internal/design-system` permanece solo en desarrollo y sin enlaces. | Cumplido |
| M10.2-AC-009 | El frontend compila correctamente. | Cumplido |

## Riesgos

- Cambiar etiquetas de navegacion no debe confundirse con agregar nuevas paginas.
- El shell no debe reemplazar la seguridad backend ni los guards existentes.
- La navegacion mobile debe evitar scroll horizontal y mantener cierre claro.
- El contenido interno actual puede seguir teniendo estilo de MVP hasta submodulos 10.3 a 10.6.

## Validacion minima

- `docker-compose exec -T frontend npm run build`.
- Revision manual de cliente, profesional y administrador.
- Revision de ruta activa.
- Revision de logout.
- Revision mobile aproximada 390-430px con drawer cerrado y abierto.
- Verificar que no haya enlaces visibles a `/internal/design-system`.

## Areas afectadas

- `frontend/src/layouts/DashboardLayout.tsx`
- `frontend/src/components/shell/*`
- `frontend/src/config/navigation.ts`
- `frontend/src/routes/router.tsx` solo si fuera indispensable.
- `specs/modules/module-10-ux-ui-redesign/submodules/10.2-shell-navigation/*`
