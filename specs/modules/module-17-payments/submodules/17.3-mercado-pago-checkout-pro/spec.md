# Submodulo 17.3 - Mercado Pago Checkout Pro

## Objetivo

Agregar Mercado Pago Checkout Pro como primer provider real de pagos, sin reemplazar el provider fake y sin procesar tarjetas dentro de RealMeet.

## Decision Checkout Pro

RealMeet crea una preferencia de Checkout Pro y entrega una URL de redireccion al cliente. El pago se realiza fuera de RealMeet. El retorno del navegador es informativo; la fuente de verdad es backend al consultar Mercado Pago o procesar Webhook.

## Configuracion

Se usa `Integration` con `integration_type=payment` y `provider=mercado_pago`. La configuracion no secreta incluye ambiente `sandbox`, pais `CL`, moneda `CLP`, `notification_url`, URLs de retorno y `auto_return=approved`.

## Credenciales

Las credenciales viven como referencias de entorno: `access_token_reference` y `webhook_secret_reference`. RealMeet rechaza access tokens directos en config y no retorna valores resueltos al frontend.

## Preferencia

Al enviar una orden `mercado_pago`, RealMeet crea una preferencia con item CLP, `external_reference=payment-order-{id}`, metadata minima y `X-Idempotency-Key` estable por orden/operacion. Se persisten `external_preference_id`, URLs de checkout y estado provider resumido.

## Checkout

El cliente autenticado puede consultar checkout de su orden. Para Mercado Pago recibe monto, moneda, estado, vencimiento y `checkout_url`. No recibe access token, payment id, preference id ni metadata tecnica.

## Retorno

Frontend expone `/payments/success`, `/payments/pending` y `/payments/failure` como vistas informativas. No aprueban pagos por si solas.

## Webhooks

`POST /api/v1/webhooks/mercado-pago` valida `x-signature` usando `ts`, `v1`, `x-request-id` y `data.id` segun documentacion oficial. Cada evento se deduplica en `MercadoPagoWebhookEvent`; eventos invalidos no cambian pagos.

## Verificacion Mediante API

El Webhook no confia en el body para aprobar. Consulta `get_payment` en Mercado Pago y ubica la orden por metadata, `external_reference` o payment id.

## Estados

Mapeo centralizado:

- `approved` -> `approved`
- `pending` -> `pending`
- `in_process` / `authorized` -> `requires_action`
- `rejected` -> `rejected`
- `cancelled` -> `cancelled`
- `refunded` -> `refunded`
- `charged_back` -> `failed`

Estados desconocidos quedan con `payment_provider_status_unknown` y revision manual.

## Idempotencia

Reintentar checkout no duplica preferencias si ya existe `external_preference_id` y URL. Webhooks duplicados no repiten transiciones ni efectos de reserva. La publicacion de eventos de pago es idempotente por orden/evento.

## Retry

Retry manual se cubre con `submit` para preferencia y `sync-provider` para consulta. No hay retries automaticos.

## Reconcile

`POST /api/v1/admin/payment-orders/{id}/reconcile` sincroniza primero provider cuando hay payment id activo y luego reutiliza las reglas 17.2. No reabre reservas canceladas.

## Seguridad

Sin tarjetas, sin tokens en frontend, sin respuestas crudas, sin payloads clinicos en preferencias, firma Webhook con comparacion segura, URLs validadas y errores sanitizados.

## Fuera De Alcance

Produccion real, cobros reales en pruebas, Checkout API con tarjetas, Payment Brick, CardForm, OAuth multi-vendedor, split payments, marketplace, comisiones, payouts, Webpay, Stripe, PayPal, reembolsos, chargeback completo, conciliacion financiera, scheduler, workers, Redis, Celery, colas, retries automaticos, facturacion, impuestos, suscripciones, despliegue y 17.4.

## Pruebas

`backend/tests/test_mercado_pago_checkout_pro.py` usa fake client e incluye configuracion, permisos, URL insegura, health, preferencia, idempotencia, checkout propietario, Webhook firmado/deduplicado, sync-provider, mapeo de estados, aplicacion a reservas, reconcile y sanitizacion.

## Resultado

17.3 deja Checkout Pro integrado de punta a punta en modo sandbox/fake-client para pruebas, listo para conectar credenciales reales de prueba mediante variables de entorno.

## Limitaciones

La integracion real depende de configurar URLs publicas HTTPS y secretos en el entorno. No se habilita produccion automaticamente ni se implementa conciliacion financiera.
