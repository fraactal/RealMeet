# Ejemplos n8n para RealMeet

RealMeet puede activar workflows de n8n mediante eventos firmados. Los workflows se configuran y ejecutan fuera de RealMeet.

## Configuracion rapida

1. En RealMeet, crea una integracion `n8n` desde el backoffice de Integraciones.
2. Configura `base_url` con la URL publica de tu instancia n8n, por ejemplo `https://automation.example.com`.
3. Importa uno de los JSON en `docs/n8n/examples/` dentro de n8n.
4. Copia el path del nodo Webhook importado, por ejemplo `realmeet/google-sheets/appointments`.
5. En RealMeet, registra un workflow n8n usando ese path relativo.
6. Selecciona los eventos recomendados por el ejemplo.
7. Define solo la referencia de secreto, por ejemplo `REALMEET_N8N_WEBHOOK_SECRET`.
8. Habilita el workflow y ejecuta una prueba desde RealMeet.
9. Revisa las entregas recientes en el backoffice.

## Firma

RealMeet envia la firma HMAC en `X-RealMeet-Signature` y el timestamp en `X-RealMeet-Timestamp`.
El secreto debe existir como variable de entorno del backend de RealMeet y tambien debe estar disponible en n8n si validas la firma dentro del workflow.

Headers enviados:

- `X-RealMeet-Signature`
- `X-RealMeet-Event`
- `X-RealMeet-Delivery`
- `X-RealMeet-Timestamp`

## Placeholders

Reemplaza antes de usar:

- `REPLACE_WITH_GOOGLE_SHEET_DOCUMENT_ID`
- `REPLACE_WITH_SHEET_NAME`
- `REPLACE_WITH_N8N_CREDENTIAL_ID`
- `REPLACE_WITH_GOOGLE_SHEETS_OAUTH2`
- `https://crm.example.com/api/contacts/upsert`
- `https://internal-notifications.example.com/hooks/realmeet`

Los ejemplos no contienen credenciales y no deben usarse en produccion sin revisar seguridad, autenticacion, permisos y manejo de errores.
