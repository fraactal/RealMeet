# Submodulo 16.2 - Exportacion manual de reservas a Google Sheets

## Objetivo

Permitir que un administrador configure y ejecute manualmente exportaciones estandar de reservas RealMeet hacia Google Sheets, complementando n8n para automatizaciones personalizadas.

## Configuracion

Modelo `GoogleSheetsExportConfig`:

- integracion Google;
- nombre;
- `spreadsheet_id`;
- `sheet_name`;
- habilitacion;
- modo `upsert` o `append_only`;
- inclusion de canceladas;
- ultimos estados de exportacion.

El `spreadsheet_id` se normaliza desde ID o URL de Google Sheets, pero se almacena solo el ID.

## Columnas

Columnas estables:

- `realmeet_appointment_id`;
- `status`;
- `starts_at`;
- `ends_at`;
- `timezone`;
- `professional_name`;
- `professional_email`;
- `client_name`;
- `client_email`;
- `meeting_provider`;
- `meeting_url`;
- `created_at`;
- `updated_at`;
- `cancelled_at`.

## Privacidad

No se exportan notas clinicas, diagnosticos, motivo de consulta, historial medico, telefonos, tokens, configuraciones internas ni payloads tecnicos.

## Idempotencia

La clave estable es `realmeet_appointment_id`.

## Upsert

Si la reserva ya existe, se actualiza la fila. Si no existe, se agrega. No duplica filas.

## Append

Solo agrega reservas nuevas. Si la reserva ya existe, se omite. No duplica filas.

## Encabezados

El servicio valida metadata, pestana y encabezados:

- crea encabezados si la hoja esta vacia;
- acepta encabezados compatibles;
- agrega columnas faltantes al final;
- rechaza encabezados incompatibles con `google_sheets_incompatible_headers`.

## Historial

Modelo `GoogleSheetsExportExecution` registra estado, rango, solicitante, conteos y error resumido.

## Retry

El retry manual crea una nueva ejecucion usando configuracion y rango originales. Mantiene idempotencia y no sobrescribe ejecuciones previas.

## Fuera de alcance

No hay exportacion automatica, workers, colas, importacion desde Sheets, sincronizacion bidireccional, selector Drive, creacion de spreadsheets, dashboards ni integracion nueva con n8n.

## Criterios de aceptacion

- Admin configura hoja destino.
- Profesional y cliente quedan bloqueados.
- Sheets deshabilitado o sin scope falla con error claro.
- Validacion confirma spreadsheet, pestana y encabezados.
- Exportacion manual escribe filas.
- `upsert` y `append_only` no duplican.
- Historial y retry quedan disponibles.
- Frontend compila.
- Pruebas especificas pasan.

## Pruebas

Archivo: `backend/tests/test_google_sheets_exports.py`.

Se usa fake Sheets client y no se hacen llamadas reales a Google.

## Resultado

Implementado para revision en 16.2.

## Limitaciones

La ejecucion es sincrona y limitada a 1000 reservas por corrida y 366 dias por rango. La exportacion asincrona queda para una fase posterior.
