# RealMeet visual system

## Concepto

RealMeet debe sentirse como una plataforma SaaS profesional, calmada y confiable para salud, servicios clinicos, legales y otras categorias profesionales.

El sistema visual prioriza:

- confianza;
- privacidad;
- claridad operativa;
- lectura rapida de reservas, estados y acciones;
- una identidad propia sin apariencia hospitalaria fria.

## Paleta

| Token | Uso | Valor |
| --- | --- | --- |
| `brand` | Acciones principales, foco visual, navegacion futura | `#0b5563` |
| `brand-600` | Hover primario | `#0f6b78` |
| `brand-100` | Superficies suaves de marca | `#d9f0f2` |
| `surface-page` | Fondo general | `#f6f3ee` |
| `surface-card` | Tarjetas y paneles | `#ffffff` |
| `ink-900` | Texto principal | `#102a43` |
| `ink-700` | Texto secundario fuerte | `#334e68` |
| `ink-500` | Metadatos y ayuda | `#627d98` |
| `success` | Completado, activo, correcto | `#17633a` |
| `warning` | Pendiente, requiere atencion | `#8a5a00` |
| `danger` | Cancelado, error, accion destructiva | `#9f2a2a` |
| `info` | Confirmado, informacion neutral relevante | `#1e5b8f` |

## Tipografia

La fuente base usa el stack del sistema con prioridad para `Inter` si esta disponible en el navegador. No se agrega una dependencia tipografica.

Escala base:

- titulo de pagina: `text-2xl` a `text-3xl`, `font-bold`;
- seccion: `text-lg`, `font-semibold`;
- cuerpo: `text-sm` o `text-base`;
- ayuda/metadatos: `text-sm`, `text-ink-500`;
- badges: `text-xs`, `font-semibold`.

## Espaciado

Se usa la escala Tailwind existente para evitar tokens paralelos:

- tarjetas: `p-5` o `p-6`;
- separacion interna compacta: `gap-2`, `gap-3`;
- separacion entre bloques: `gap-4`, `gap-6`;
- encabezados de pagina: margen inferior `mb-6`.

## Bordes, radios y sombras

- radios principales: `rounded-md` para controles y `rounded-lg` para tarjetas;
- bordes suaves: `border-slate-200/80`;
- sombra base: `shadow-soft`;
- sombra elevada disponible: `shadow-lift`.

## Componentes base

Implementados en `frontend/src/components/ui`:

- `Button`;
- `Input`;
- `Select`;
- `Textarea`;
- `Label`;
- `Card`;
- `SectionCard`;
- `Badge`;
- `StatusBadge`;
- `Avatar`;
- `PageHeader`;
- `EmptyState`;
- `LoadingState`;
- `ErrorState`;
- `Icon`.

## Botones

Variantes:

- `primary`: accion principal;
- `secondary`: accion secundaria;
- `ghost`: accion contextual de bajo peso;
- `danger`: accion destructiva o cancelacion.

Tamanos:

- `sm`;
- `md`;
- `lg`.

Los botones soportan estado `isLoading`.

## Inputs

Los controles comparten:

- borde claro;
- foco visible;
- fondo blanco;
- estados disabled;
- `rounded-md`;
- `focus:ring-brand-100`.

## Badges y estados

Los estados de reserva se muestran mediante `StatusBadge` y helpers centralizados:

| API | UI |
| --- | --- |
| `pending` | Pendiente |
| `confirmed` | Confirmada |
| `cancelled` | Cancelada |
| `completed` | Completada |
| `no_show` | No asistio |

Modalidad:

| API | UI |
| --- | --- |
| `online` | Online |
| `in_person` | Presencial |
| `presencial` | Presencial |
| `hybrid` | Hibrida |

Meeting:

| API | UI |
| --- | --- |
| `active` | Reunion disponible |
| `inactive` | Reunion inactiva |
| `pending` | Reunion pendiente |
| `unknown` | Estado de reunion no disponible |

## Fechas

Los helpers usan `Intl.DateTimeFormat` con locale `es-CL`:

- `formatLongDate`: miercoles 15 de julio;
- `formatCompactDate`: 15 jul 2026;
- `formatTime`: 10:00 h;
- `formatDateTime`: 15 jul 2026 - 10:00 h.

No se agrega libreria externa de fechas.

## Iconografia

Se implementa `Icon` como componente SVG interno para evitar dependencia nueva en 10.1.

Iconos disponibles:

- `calendar`;
- `chart`;
- `check`;
- `clock`;
- `dashboard`;
- `filter`;
- `logout`;
- `search`;
- `settings`;
- `user`;
- `users`.

Si el rediseño posterior requiere una libreria completa, `lucide-react` puede evaluarse en un submodulo posterior verificando licencia antes de incorporarla.

## Accesibilidad base

- foco visible global;
- botones con estado disabled;
- `ErrorState` con `role="alert"`;
- `Icon` puede recibir `title` si necesita nombre accesible;
- no se depende solo del color porque los badges incluyen texto.
