# Submodulo 16.3 - Google Docs, plantillas y almacenamiento en Drive

## Objetivo

Agregar generacion manual de documentos operativos desde plantillas Google Docs, almacenando el resultado en Drive y vinculandolo a reservas RealMeet.

## Tipos de documentos

Permitidos:

- `appointment_summary`
- `appointment_confirmation`
- `pre_session_instructions`
- `post_session_instructions`
- `administrative_receipt`
- `custom_operational`

No se habilitan documentos clinicos.

## Privacidad

El submodulo no exporta ni inserta notas clinicas, diagnosticos, historia medica, motivos clinicos, prescripciones, tokens ni contenido completo de documentos.

## Catalogo de variables

Las variables estan centralizadas en `VARIABLE_REGISTRY`. Las variables bloqueadas incluyen `clinical_notes`, `diagnosis`, `medical_history`, `session_notes`, `password` y `token`.

## Validacion

La validacion revisa:

- integracion Google;
- Docs y Drive habilitados;
- scopes autorizados;
- metadata del documento fuente;
- carpeta destino opcional;
- placeholders permitidos.

No retorna contenido completo del documento.

## Copia y reemplazo

La generacion:

1. copia la plantilla con Drive API;
2. mueve la copia a la carpeta destino si existe;
3. reemplaza variables con `replaceAllText` de Google Docs API;
4. no modifica la plantilla origen.

## Drive y permisos

Politicas:

- `private`
- `professional_only`
- `professional_and_client`

Solo se crean permisos `reader` para usuarios especificos. No se permite `writer` ni acceso publico.

## Idempotencia

Se usa `appointment_id`, `template_id` y `generation_request_id` para impedir duplicados accidentales.

## Retry

El retry manual trabaja sobre documentos `failed`, `partially_generated` o `reconcile_required`. Si ya existe `external_file_id`, no copia nuevamente y continua con reemplazos/permisos.

## Reconcile

La reconciliacion comprueba existencia y tipo del documento externo, y actualiza estado local sin sobrescribir reservas.

## Fuera de alcance

No hay generacion automatica, area profesional/cliente, PDFs, firmas, Gmail, WhatsApp, editor de Docs, subida de archivos, seleccion visual de Drive, workers, colas ni Microsoft 365.

## Criterios de aceptacion

- Admin registra plantillas.
- Variables centralizadas sin variables clinicas.
- Documento y carpeta se validan.
- Se copia plantilla sin modificar origen.
- Se reemplazan variables.
- Documento queda vinculado a reserva.
- Permisos son reader y no publicos.
- Retry y reconcile existen.
- Errores quedan sanitizados.
- Frontend permite operar plantillas y documentos por reserva.

## Pruebas

Archivo: `backend/tests/test_google_docs_templates.py`.

Usa fake Drive y fake Docs clients. No realiza llamadas reales a Google.

## Resultado

Implementado para revision de 16.3.

## Limitaciones

OAuth Google sigue siendo administrativo/global. La generacion es manual y sin workers. La verificacion de permisos externos en reconcile es basica y se ampliara cuando exista auditoria documental avanzada.
