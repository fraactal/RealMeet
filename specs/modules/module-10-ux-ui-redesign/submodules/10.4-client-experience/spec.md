# Submodulo 10.4 - Experiencia cliente

## Objetivo

Redisenar la experiencia autenticada del cliente para que pueda revisar sus reservas, buscar profesionales y completar el flujo de reserva con informacion clara, sin cambiar reglas de negocio ni contratos de backend.

## Alcance

- Dashboard cliente en `/dashboard`.
- Mis reservas en `/dashboard/appointments`.
- Busqueda, perfil publico, seleccion de horario y creacion de reserva en `/professionals`.
- Componentes reutilizables bajo `frontend/src/components/client/`.
- Estados de carga, error y vacio con componentes globales.
- Traduccion de estados, modalidad y reunion usando helpers existentes.

## Fuera de alcance

- Cambios backend, APIs, migraciones o permisos.
- Reprogramacion, pagos, chat, mensajes, resenas, ratings o videollamada real.
- Redisenos profesional, administrativo, landing o shell global.
- Nueva pagina de perfil cliente, porque no existe una ruta funcional actual.

## Rutas afectadas

- `/dashboard`
- `/dashboard/appointments`
- `/professionals`

## Datos reales utilizados

- `/client/metrics`: conteos por estado, proximas reservas y reservas recientes.
- `/appointments/me`: reservas del cliente, estado, fechas, modalidad, reunion, notas del cliente e historial.
- `/professionals`: profesionales publicos, categoria, especialidades, modalidad, ciudad/pais y paginacion.
- `/professionals/:id`: detalle publico del profesional.
- `/professionals/:id/availability`: horarios disponibles por fecha.
- `/appointments`: creacion de reserva con profesional, especialidad filtrada y fecha seleccionada.

## Componentes previstos

- `ClientAppointmentCard`
- `ClientQuickActions`
- `ClientStatSummary`
- `ProfessionalSearchCard`
- `SlotPicker`

## Riesgos

- El contrato de reservas cliente no entrega nombre del profesional, por lo que la UI usa un texto neutral y no inventa identidad.
- El perfil cliente editable existe como API, pero no como ruta visible; se deja fuera del alcance.
- La disponibilidad depende de datos existentes y puede aparecer vacia segun configuracion local.

## Validacion minima

- `docker-compose exec -T frontend npm run build`
- Revision manual de dashboard cliente, busqueda, detalle profesional, seleccion de horario, creacion de reserva, mis reservas y cancelacion existente.
- Capturas desktop y mobile representativas.
