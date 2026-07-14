# Diseno tecnico del Modulo 3

## Modelos existentes

- `Category`: `id`, `name`, `slug`, `description`, `is_active`, timestamps.
- `Specialty`: `id`, `category_id`, `name`, `slug`, `description`, `is_active`, timestamps.
- `ProfessionalProfile`: contiene categoria, datos publicables, `is_verified`, `is_public`, precio y licencia.
- `ProfessionalSpecialty`: relacion entre perfil profesional y especialidad.

## Migracion prevista

Agregar una restriccion unica para `professional_specialties(professional_id, specialty_id)` si la base actual no contiene duplicados. Antes de crearla debe inspeccionarse que no existan duplicados.

No se esperan nuevas columnas. `is_public`, `is_active`, categorias y especialidades ya existen.

## Contratos

Categorias:

- `CategoryPublicRead`: sin `is_active`.
- `CategoryAdminRead`: incluye `is_active`.
- `CategoryCreate`.
- `CategoryUpdate`.

Especialidades:

- `SpecialtyPublicRead`: sin `is_active`, con categoria basica.
- `SpecialtyAdminRead`: incluye `is_active`.
- `SpecialtyCreate`.
- `SpecialtyUpdate`.

Profesional:

- `ProfessionalSpecialtyRead`.
- `ProfessionalSpecialtyUpdate`.
- `ProfessionalPublicName`.
- `ProfessionalPublicListItem`.
- `ProfessionalPublicDetail`.
- `ProfessionalPublicProfileUpdate`.
- `PaginatedProfessionalPublicResponse`.

## Endpoints publicos

- `GET /categories`: categorias activas.
- `GET /specialties`: especialidades activas, opcionalmente por categoria activa.
- `GET /professionals`: respuesta paginada con filtros.
- `GET /professionals/{professional_id}`: detalle publico solo si cumple reglas de publicacion.

## Endpoints profesionales

- `GET /professionals/me/specialties`.
- `PATCH /professionals/me/specialties`.
- `GET /professionals/me/public-profile`.
- `PATCH /professionals/me/public-profile`.

## Endpoints administrativos

- `GET /admin/categories`.
- `POST /admin/categories`.
- `PATCH /admin/categories/{category_id}`.
- `GET /admin/specialties`.
- `POST /admin/specialties`.
- `PATCH /admin/specialties/{specialty_id}`.

Los endpoints write existentes en `/categories` y `/specialties` pueden mantenerse por compatibilidad, pero el frontend admin usara `/admin/*`.

## Reglas de publicacion

La consulta publica usa un predicado comun:

```text
User.role == professional
User.is_active == true
ProfessionalProfile.is_public == true
ProfessionalProfile.title no vacio
ProfessionalProfile.category activa
al menos una specialty activa
```

## Paginacion

Contrato:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0,
  "total_pages": 0
}
```

`page_size` maximo: 50.

## Frontend

- Reutilizar TanStack Query.
- `ProfessionalsPage` consume filtros y paginacion.
- Agregar detalle publico.
- Agregar paginas dashboard para gestion profesional y admin catalogo.
- Mantener backend como autoridad; frontend no es control de seguridad.

## Validacion

- Pruebas backend pequenas para contratos, permisos, filtros y relaciones.
- Build frontend.
- Runtime con Docker Compose v1.
- Logs acotados sin `-f`.
