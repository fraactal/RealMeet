# Modulo 3: Catalogo profesional y busqueda publica

## Contexto

RealMeet ya tiene autenticacion, autorizacion y perfiles base verificados hasta el Modulo 2. Existen modelos iniciales de catalogo profesional y un listado publico parcial de profesionales, pero todavia no hay contratos separados por contexto, paginacion ni gestion completa de catalogo.

## Problema

La inspeccion inicial confirma que el catalogo esta parcialmente implementado:

- `Category`, `Specialty`, `ProfessionalProfile` y `ProfessionalSpecialty` existen.
- `GET /categories`, `GET /specialties`, `GET /professionals` y `GET /professionals/{id}` existen.
- Las rutas publicas de profesionales usan `UserRead`, que expone `email`, `is_active`, `created_at` y `updated_at`.
- El detalle publico por ID no valida `is_public`.
- `GET /professionals` no tiene paginacion.
- No existe restriccion DB unica para `(professional_id, specialty_id)`.
- La gestion admin de categorias/especialidades existe parcialmente en rutas publicas con writes protegidos, pero no hay rutas `/admin/categories` ni `/admin/specialties`.
- No existe UI de gestion profesional de especialidades/publicacion ni UI admin minima de catalogo.

## Objetivo

Implementar un catalogo profesional seguro y funcional que permita gestionar categorias y especialidades, asociar profesionales con especialidades, publicar u ocultar perfiles, listar y filtrar profesionales publicos y administrar el catalogo minimo sin avanzar a disponibilidad, slots ni reservas.

## Alcance

- Categorias y especialidades activas en lectura publica.
- Contratos separados para publico, admin y profesional.
- Administracion minima de categorias y especialidades.
- Especialidades propias del profesional.
- Perfil publico profesional seguro.
- Publicacion u ocultamiento con reglas explicitas.
- Busqueda publica con filtros y paginacion acotada.
- Frontend publico del catalogo.
- Frontend profesional para campos publicos/especialidades/publicacion.
- Frontend admin minimo para categorias y especialidades.
- Pruebas minimas y validacion runtime.
- Documentacion SDD y trazabilidad.

## Exclusiones

- Disponibilidad semanal.
- Calculo de slots.
- Bloqueos manuales.
- Reservas.
- Calendario.
- Reuniones.
- Pagos, precios complejos, promociones y suscripciones.
- Ratings, resenas y favoritos.
- Busqueda geoespacial o motor externo.
- IA.
- Verificacion clinica, documentos clinicos o carga de certificados.
- Backoffice completo.
- Pruebas E2E complejas, carga, estres o rendimiento.

## Actores

- Usuario publico: lista categorias, especialidades y profesionales publicados.
- `admin`: gestiona categorias y especialidades.
- `professional`: gestiona sus especialidades, campos publicos autorizados y visibilidad.
- `client`: puede navegar catalogo publico, pero no gestionar catalogo.

## Reglas de catalogo

- Categorias y especialidades inactivas no aparecen publicamente.
- Solo `admin` puede crear o actualizar categorias/especialidades.
- El nombre es obligatorio.
- Slugs se derivan del nombre.
- No se permiten duplicados segun las restricciones actuales: categoria por `name`/`slug`, especialidad por `slug`.
- No hay eliminacion destructiva en este modulo.

## Reglas de especialidades del profesional

- Un profesional solo modifica su propio perfil.
- Solo puede asignarse especialidades existentes y activas.
- No se permiten relaciones duplicadas.
- La actualizacion debe reemplazar el conjunto de especialidades de forma transaccional.

## Reglas de publicacion

Un profesional aparece publicamente solo si:

- el usuario esta activo;
- el usuario tiene rol `professional`;
- existe `ProfessionalProfile`;
- `is_public` es `true`;
- el perfil cumple minimos del modulo: titulo, categoria activa y al menos una especialidad activa.

No se exige `is_verified`, porque no existe regla validada que lo requiera.

## Contratos publicos

Los contratos publicos no deben exponer:

- email;
- telefono;
- `is_active`;
- `created_at`/`updated_at`;
- `user_id`;
- `professional_license`;
- `is_verified`;
- precio;
- hashes, tokens, secretos, notas o datos clinicos.

Campos publicos permitidos:

- `id` de perfil profesional;
- nombre visible;
- titulo;
- biografia;
- modalidad;
- duracion de sesion;
- ciudad y pais;
- categoria activa;
- especialidades activas.

## Filtros y paginacion

Filtros esperados:

- `search`;
- `category_id`;
- `specialty_id`;
- `modality` si el campo existe;
- `page`;
- `page_size`.

Reglas:

- `page >= 1`;
- `page_size` acotado entre 1 y 50;
- orden estable por nombre de usuario y `ProfessionalProfile.id`;
- sin resultados devuelve `items=[]`;
- no hay consultas publicas ilimitadas.

## Seguridad y riesgos

- Datos protegidos: emails privados, telefonos, estado interno, licencias, verificaciones, precios, notas, hashes y tokens.
- Amenazas identificadas: exposicion de `UserRead`, perfiles ocultos por ID, asignacion de especialidades inactivas, duplicados, mass assignment admin y consultas sin limite.
- Controles previstos: schemas explicitos, servicios con validacion, constraint unica, paginacion, rutas por rol y pruebas minimas.
- Riesgos aceptados temporalmente: busqueda por `ilike` sobre PostgreSQL sin motor externo.
- Deuda prevista: optimizaciones de indices de busqueda si el volumen lo exige.

## Fases

1. Baseline y diseno del catalogo.
2. Categorias y especialidades backend.
3. Especialidades propias del profesional.
4. Perfil publico profesional backend.
5. Busqueda, filtros y paginacion backend.
6. Frontend publico del catalogo.
7. Gestion profesional y administrativa minima.
8. Validacion integrada y cierre.

## Definition of Done

El modulo termina cuando categorias, especialidades, perfiles publicos, busqueda, filtros, paginacion, UI publica, UI profesional, UI admin minima, permisos, pruebas, build, health/ready, trazabilidad y documentacion esten validados, cada fase tenga commit independiente, no se haya hecho push y no se haya avanzado al Modulo 4.
