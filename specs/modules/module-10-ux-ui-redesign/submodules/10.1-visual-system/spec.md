# Submodulo 10.1 - Sistema visual global

## Objetivo

Crear la base visual reutilizable de RealMeet antes de rediseñar pantallas especificas.

## Alcance

Este submodulo implementa:

- paleta;
- tipografia;
- tokens visuales;
- espaciado base;
- bordes, radios y sombras;
- botones;
- inputs;
- selects;
- textarea;
- cards;
- badges;
- iconografia base;
- helpers de fechas;
- traduccion de enums;
- estados de loading, error y vacio.

## Fuera de alcance

No se implementa todavia:

- shell y navegacion;
- dashboards por rol;
- landing;
- catalogo publico;
- rediseño completo de paginas;
- cambios backend;
- dependencias nuevas.

## Decisiones tecnicas

- Se mantiene Tailwind CSS como fuente principal de tokens.
- Se conserva compatibilidad con clases existentes como `text-ink`, `bg-brand`, `bg-mist` y `text-brand`.
- No se agrega libreria de iconos en 10.1; se crea un componente SVG interno minimo.
- Los helpers de fechas usan APIs nativas del navegador con locale `es-CL`.
- Las traducciones de enums quedan centralizadas en `frontend/src/utils/labels.ts`.

## Archivos principales

- `frontend/tailwind.config.js`
- `frontend/src/styles.css`
- `frontend/src/components/ui/*`
- `frontend/src/utils/cn.ts`
- `frontend/src/utils/dates.ts`
- `frontend/src/utils/labels.ts`
- `specs/modules/module-10-ux-ui-redesign/visual-system.md`
