# RealMeet secrets inventory

Este inventario registra categorias y referencias. No contiene valores reales.

| secreto logico | variable o referencia | consumidor | ambiente | obligatorio | activacion | provision prevista | rotacion | evidencia de no exposicion | si falta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JWT signing key | `SECRET_KEY` | backend auth | todos | si | arranque API | env/secret store del hosting | rotar invalidando sesiones | staging rechaza placeholders; no se expone en API | backend no arranca/readiness falla |
| PostgreSQL URL | `DATABASE_URL` | backend DB | todos | si | arranque API, migraciones | env/secret store | rotar password DB y redeploy | `.env` ignorado; templates sin credencial real | backend/readiness falla |
| PostgreSQL password compose | `POSTGRES_PASSWORD` | contenedor DB local/staging local | docker/staging local | si en compose | DB local | env local no versionado | recrear credencial DB | `.env.staging.example` usa placeholder | DB no acepta conexiones |
| SMTP password | `SMTP_PASSWORD` | email service | staging/production | opcional | `EMAIL_MODE=smtp` | env/secret store | rotar en SMTP y redeploy | log mode por defecto; no se imprime | email SMTP falla o modo log |
| Google OAuth client secret | `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth admin Google | staging/production | condicional | OAuth configurado | env/secret store | rotar en Google Cloud | settings exige OAuth completo; no se muestra token | OAuth no disponible |
| Google token encryption key | `GOOGLE_TOKEN_ENCRYPTION_KEY` | cifrado tokens Google | staging/production | condicional | OAuth configurado | env/secret store | plan con re-cifrado controlado | tokens no se exponen por API | OAuth no disponible |
| Google refresh/access tokens | cifrados en DB | servicios Google | staging/production | condicional | integracion conectada | OAuth consentido por admin | revocar en Google y reconectar | cifrados, no se muestran en UI | integracion requiere reconexion |
| WhatsApp access token | `WHATSAPP_ACCESS_TOKEN` o referencia | WhatsApp client | staging/production | condicional | `WHATSAPP_CLOUD_ENABLED=true` o integracion habilitada | env/secret store | rotar en Meta y redeploy | UI muestra referencia, no valor | envio/health falla sanitizado |
| WhatsApp app secret | `WHATSAPP_APP_SECRET` | webhook WhatsApp | staging/production | condicional | firma webhook requerida | env/secret store | rotar en Meta y actualizar env | HMAC con compare_digest, no se persiste firma | webhooks firmados se rechazan |
| WhatsApp verify token | `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | webhook verification | staging/production | condicional | alta webhook Meta | env/secret store | rotar en Meta y env | compare_digest, no se retorna salvo challenge valido | verificacion webhook falla |
| WhatsApp phone HMAC key | `WHATSAPP_PHONE_HMAC_KEY` | consentimiento/correlacion | staging/production | condicional | WhatsApp enabled | env/secret store | rotacion con estrategia de hashes | telefonos completos no salen en API admin | consent/correlacion falla |
| Mercado Pago access token | `MERCADO_PAGO_ACCESS_TOKEN` por referencia | pagos provider | sandbox/production | condicional | integracion Mercado Pago | env/secret store | rotar en Mercado Pago | config guarda referencia y parse rechaza secretos directos | pagos/sync fallan sanitizado |
| Mercado Pago webhook secret | `MERCADO_PAGO_WEBHOOK_SECRET` por referencia | webhook pagos | sandbox/production | condicional | webhook configurado | env/secret store | rotar en Mercado Pago | firma verificada, no se imprime | webhook queda invalid_signature/failed |
| Webhook outgoing secret | `REALMEET_WEBHOOK_SECRET` por referencia | webhooks salientes | staging/production | condicional | suscripcion habilitada | env/secret store | rotar referencia y reintentar | se firma en memoria, no body completo | entrega falla configuracion |
| n8n webhook secret | `REALMEET_N8N_WEBHOOK_SECRET` por referencia | automatizacion n8n | staging/production | condicional | workflow habilitado | env/secret store | rotar referencia/workflow | path relativo, firma HMAC | workflow no recibe entrega valida |

## Estrategia

- Desarrollo local puede usar `.env` no versionado.
- CI usa valores ficticios sin `secrets.*`.
- Staging/production deben cargar valores reales desde el entorno seguro de la plataforma.
- Las referencias deben ser nombres de variables, no secretos.
- No se implementa proveedor cloud en H2.
