# Modulo 4 - Disponibilidad semanal, bloqueos y calculo de horarios

## Problema

El sistema tenia modelos y endpoints parciales de disponibilidad, pero no cubria administracion completa de reglas/bloqueos propios, validaciones de solapamiento, limites de consulta ni una experiencia frontend para profesionales y publico.

## Objetivo

Permitir que un profesional configure disponibilidad semanal y bloqueos manuales, y que usuarios publicos consulten horarios disponibles sin crear reservas.

## Alcance

- Reglas semanales propias del profesional.
- Bloqueos manuales propios.
- Calculo publico de slots por fecha o rango corto.
- Exclusion de slots bloqueados, ocupados y pasados.
- UI profesional basica para reglas y bloqueos.
- UI publica basica de horarios en detalle profesional.

## Exclusiones

- Crear reservas.
- Pagos, correos, reuniones reales, calendario externo, recurrencia avanzada, feriados y zonas horarias internacionales.
- Pruebas exhaustivas de fechas o rendimiento.

## Actores

- Profesional autenticado.
- Usuario publico o cliente consultando disponibilidad.

## Reglas de negocio

- `weekday` usa 0=lunes a 6=domingo.
- `start_time` debe ser menor que `end_time`.
- Un profesional no puede tener reglas activas solapadas para el mismo dia.
- Un bloqueo debe tener `start_datetime < end_datetime`.
- Solo el profesional propietario gestiona sus reglas y bloqueos.
- La duracion usa `ProfessionalProfile.session_duration_minutes`; si es invalida se usa 60 minutos.
- La consulta publica se limita a 14 dias.

## Modelo de datos

Se reutilizan tablas existentes:

- `availability_rules`: profesional, dia, inicio, termino, activo.
- `availability_blocks`: profesional, inicio, termino, motivo, tipo.

No se agregan columnas ni migraciones en este modulo.

## Endpoints

Profesional:

- `GET /professionals/me/availability-rules`
- `POST /professionals/me/availability-rules`
- `PATCH /professionals/me/availability-rules/{rule_id}`
- `DELETE /professionals/me/availability-rules/{rule_id}`
- `GET /professionals/me/availability-blocks`
- `POST /professionals/me/availability-blocks`
- `PATCH /professionals/me/availability-blocks/{block_id}`
- `DELETE /professionals/me/availability-blocks/{block_id}`

Publico:

- `GET /professionals/{professional_id}/availability?date=YYYY-MM-DD`
- `GET /professionals/{professional_id}/availability?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
- Compatibilidad: `start` y `end` como datetimes.

## Calculo de slots

1. Normaliza rango a UTC.
2. Obtiene reglas activas del profesional.
3. Divide cada intervalo semanal por duracion de sesion.
4. Excluye slots pasados.
5. Excluye bloqueos manuales `blocked`.
6. Excluye reservas `pending` y `confirmed` ya existentes.
7. Devuelve slots ordenados.

## Seguridad y riesgos

- Riesgos identificados: manipulacion de IDs, intervalos invalidos, solapamientos, rangos excesivos y exposicion de errores internos.
- Controles implementados: rutas profesionales protegidas, carga por propietario, validaciones de rango, solapamiento y limite de consulta.
- Riesgos pendientes: zonas horarias avanzadas, concurrencia fuerte y pruebas exhaustivas de calendario.

## Controles finales

- Backend tests.
- Frontend build.
- `/health` y `/ready`.
- Runtime minimo de reglas, bloqueos, slots y 403.
- Logs acotados.
