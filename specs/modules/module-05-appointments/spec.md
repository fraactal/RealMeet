# Modulo 5 - Reservas, estados e historial

## Problema

El sistema tenia reservas parciales: podia crear una cita y registrar historial inicial, pero no validaba el slot contra la disponibilidad del Modulo 4, no tenia proteccion de base de datos para doble reserva y permitia transiciones insuficientemente controladas.

## Objetivo

Permitir que clientes creen reservas reales usando slots disponibles y que clientes/profesionales gestionen estados basicos con historial y contratos seguros.

## Alcance

- Creacion de reserva por cliente autenticado.
- Revalidacion backend de disponibilidad.
- Prevencion de doble reserva activa.
- Listado y detalle por actor autorizado.
- Cancelacion por cliente/profesional.
- Confirmacion, completado y no show por profesional propietario.
- Notas privadas solo para profesional propietario.
- Historial de creacion y transiciones.
- Frontend cliente y profesional basico.

## Exclusiones

- Pagos, correos avanzados, reuniones reales, recordatorios, reprogramacion automatica, recurrencia, lista de espera y pruebas exhaustivas.

## Actores

- Cliente: crea, lista, consulta y cancela reservas propias futuras.
- Profesional: lista reservas propias, confirma, cancela, completa, marca no show y administra nota privada.
- Admin: consulta reservas sin notas privadas por defecto.

## Estados y transiciones

Estados existentes: `pending`, `confirmed`, `cancelled`, `completed`, `no_show`.

Transiciones MVP:

- `pending -> confirmed`
- `pending -> cancelled`
- `confirmed -> cancelled`
- `confirmed -> completed`
- `confirmed -> no_show`

`cancelled`, `completed` y `no_show` no se reabren en este modulo.

## Validacion de disponibilidad

Al crear, el backend:

1. valida cliente;
2. valida profesional publico y activo;
3. normaliza fecha UTC;
4. calcula duracion desde perfil;
5. rechaza pasado;
6. busca conflicto activo;
7. recalcula disponibilidad del rango exacto;
8. crea reserva si el slot existe.

## Prevencion de duplicados

Se combina validacion en servicio con indices unicos parciales PostgreSQL para estados `pending` y `confirmed`.

## Historial

Cada creacion y transicion registra `AppointmentHistory` con actor, estado anterior, nuevo estado, comentario y fecha.

## Seguridad y riesgos

- Riesgos: doble reserva, acceso por ID, transiciones invalidas, notas privadas expuestas, reserva fuera de disponibilidad.
- Controles: permisos por rol, contratos por actor, validacion de slot, indices parciales, historial, payload especifico para notas.
- Riesgos residuales: concurrencia intensiva y pruebas exhaustivas quedan para hardening final.

## Validaciones finales

- Backend tests.
- Frontend build.
- `/health` y `/ready`.
- Runtime: crear reserva, conflicto, listar, confirmar/cancelar, privacidad de notas, liberacion de slot.
