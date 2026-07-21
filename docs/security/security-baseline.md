# RealMeet security baseline

## Controles actuales

RealMeet usa FastAPI, JWT, PostgreSQL y React/Vite. El baseline H2 endurece configuracion, redaccion de logs y CI sin desplegar ni usar secretos reales.

## Autenticacion

- JWT firmado con `HS256`.
- `SECRET_KEY` obligatorio y rechazado si es placeholder o corto en staging/production.
- Expiracion configurable entre 5 y 1440 minutos.
- Tokens invalidos, vencidos o sin `sub` valido responden `401`.
- Usuarios inactivos no pueden iniciar sesion ni restaurar sesion.

## Autorizacion

- Dependencias por rol protegen rutas admin, professional y client.
- Clientes acceden a sus recursos.
- Profesionales acceden a su perfil, disponibilidad y reservas.
- Administradores acceden a backoffice e integraciones.
- Schemas publicos evitan hashes, tokens, fingerprints y campos internos sensibles.

## Secretos

- No se deben guardar secretos reales en Git, frontend, imagenes, docs, scripts, fixtures ni logs.
- Las plantillas contienen placeholders o valores locales no productivos.
- Las integraciones usan referencias a variables de entorno.
- La resolucion de secretos ocurre en backend y solo en memoria.

## Webhooks

- WhatsApp: verify token, HMAC SHA-256, limite de body, no persistencia de payload completo e idempotencia.
- Mercado Pago: firma, idempotencia, consulta al proveedor antes de aplicar pagos y errores publicos sanitizados.
- Webhooks salientes/n8n: firma HMAC, idempotencia, URL validada, timeout y sin redirects.

## Logging

- Logs JSON a stdout.
- Claves sensibles se redactan por nombre.
- Mensajes libres redactan bearer tokens, authorization, firmas, passwords, tokens, secrets, credentials y API keys.
- No se deben imprimir cuerpos completos de email, webhooks, documentos, datos clinicos ni credenciales.

## CORS y headers

- CORS requiere origenes explicitos; `*` se rechaza.
- Staging/production rechazan localhost salvo excepcion local controlada en staging.
- Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.
- Rutas sensibles usan `Cache-Control: no-store`.
- HSTS queda para entorno HTTPS real.

## Rate limiting

- Middleware en memoria limita login y creacion de reservas.
- Staging/production requieren `RATE_LIMIT_ENABLED=true`.
- Riesgo residual: no es distribuido; Redis, gateway o WAF quedan para fases posteriores.

## Llamadas externas

- Clientes externos usan timeouts.
- URLs de callbacks y webhooks se validan.
- No se permiten credenciales embebidas en URLs de webhooks salientes.
- Redirects salientes quedan deshabilitados donde aplica.

## Frontend

- Solo `VITE_API_URL` se expone como variable de build.
- No se deben definir secretos `VITE_*`.
- JWT en `localStorage` es deuda aceptada para produccion; requiere rediseño hacia cookies HttpOnly/SameSite y CSRF.
- UI administrativa muestra referencias/configuracion, no valores secretos.

## CI

- Workflow con `permissions: contents: read`.
- No usa `pull_request_target`.
- No usa `secrets.*`.
- `security-check` ejecuta escaneo de secretos, validacion de configuracion sensible y `npm audit --audit-level=critical`.

## Respuesta ante exposicion de secretos

1. No copiar ni mostrar el valor.
2. Identificar archivo, tipo, rama y si esta en historial.
3. Revocar/rotar en el proveedor externo.
4. Reemitir credenciales y redeploy.
5. Evaluar impacto en logs, backups y artefactos.
6. Solo despues limpiar Git si corresponde; borrar el archivo no basta.

## Practicas prohibidas

- Commitear `.env` reales.
- Pegar tokens en formularios de integracion.
- Exponer secretos al frontend.
- Registrar `Authorization`, cookies, tokens, passwords o firmas.
- Usar `pull_request_target` para CI sin revision especifica.
- Ejecutar `npm audit fix --force` o upgrades masivos sin plan.
