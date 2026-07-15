# Submodulo 10.6 - Landing y catalogo publico

## Objetivo

Redisenar la experiencia publica de RealMeet para comunicar la propuesta de valor, facilitar la busqueda de profesionales y conectar el descubrimiento con login o registro sin agregar reglas de negocio nuevas.

## Alcance

- Landing publica `/`.
- Header y footer publicos.
- Catalogo publico `/professionals`.
- Perfil publico y disponibilidad dentro del flujo de catalogo.
- Login `/login`.
- Registro cliente `/register` usando endpoint existente.
- Mini-spec y validacion visual.

## Fuera de alcance

- Cambios backend, APIs nuevas o migraciones.
- Pagos, ratings, resenas, precios, soporte, paginas legales, analytics o SEO avanzado.
- Cambios al shell autenticado o reglas de reserva.

## Rutas afectadas

- `/`
- `/professionals`
- `/login`
- `/register`

## Datos reales utilizados

- `/professionals`: profesionales publicos, categoria, especialidades, modalidad, bio, ubicacion y paginacion.
- `/professionals/:id`: perfil publico profesional.
- `/professionals/:id/availability`: horarios disponibles por fecha.
- `/auth/login`: inicio de sesion.
- `/auth/register-client`: registro cliente existente.

## Componentes previstos

- `PublicHeader`
- `PublicFooter`
- `PublicProfessionalCard`

## Riesgos

- No existe registro profesional publico; el CTA profesional se dirige a login.
- No se conserva seleccion de horario para usuarios no autenticados, porque el flujo actual no lo implementa.
- El catalogo publico comparte pagina con busqueda autenticada cliente.

## Validacion minima

- `docker-compose exec -T frontend npm run build`
- Revision manual de landing, catalogo, perfil, disponibilidad, seleccion sin sesion, login, registro, header, menu mobile y footer.
