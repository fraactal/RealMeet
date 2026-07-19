# Modulo 17 - Pagos

## Objetivo
El Modulo 17 incorpora el dominio de pagos de RealMeet para el MVP: ordenes internas de cobro, checkout fake, politicas de reserva basadas en pago, Mercado Pago Checkout Pro, webhooks firmados, sync/reconcile manual y reembolsos administrativos. RealMeet no procesa tarjetas ni almacena datos PCI.

## Commits del modulo
- `027ae71 feat(payments): add payment order foundation`
- `9c51dcb feat(payments): add fake checkout and booking policies`
- `0b666e5 feat(payments): add Mercado Pago Checkout Pro`
- `6229e3f feat(payments): add refunds and payment reconciliation`

## Arquitectura
El modulo se organiza en modelos SQLAlchemy, schemas Pydantic, servicios de dominio, routers FastAPI y providers desacoplados. Los endpoints se mantienen delgados; la logica de transiciones, idempotencia, confirmacion de reserva, sync, retry, reconcile y refunds vive en servicios.

## Modelos
- `PaymentOrder`: intencion interna de cobro con snapshot de monto, moneda, provider, estado, vencimiento, referencias externas y resumen de refund.
- `PaymentOrderStatusHistory`: historial de transiciones de orden.
- `PaymentRefund`: solicitud de reembolso total o parcial asociada a una orden aprobada.
- `PaymentRefundStatusHistory`: historial de transiciones de refund.
- `MercadoPagoWebhookEvent`: deduplicacion y auditoria de webhooks recibidos.

## Estados
Ordenes: `draft`, `pending`, `requires_action`, `approved`, `rejected`, `cancelled`, `expired`, `failed`, `refunded`.

Refunds: `requested`, `processing`, `approved`, `rejected`, `cancelled`, `failed`, `reconcile_required`.

Reservas agrega `pending_payment` para bloquear el slot mientras espera pago antes de confirmar.

## Montos y moneda
La moneda soportada en el MVP es `CLP`. Los montos usan `Decimal`, deben ser positivos y CLP no acepta fracciones. Los reembolsos parciales acumulados no pueden superar el monto pagado.

## Provider fake
`fake` soporta creacion de orden, checkout autenticado de cliente, aprobacion, rechazo, expiracion, fallo controlado y controles administrativos de refund. Solo se usa para pruebas funcionales y demostracion; no cobra dinero real.

## Mercado Pago Checkout Pro
Mercado Pago se configura como `Integration` de tipo `payment`. Checkout Pro se usa por redireccion: RealMeet crea preferencias, guarda `external_preference_id`, URLs de checkout y estado provider resumido. El Access Token se resuelve solo por referencia de entorno en backend.

## Webhooks
El webhook de Mercado Pago valida firma HMAC, deduplica por `event_id`, consulta el pago en provider antes de aplicar estado y registra resultado. Webhooks de refund se registran como `refund_sync_required` para sync/reconcile manual en 17.4/17.5.

## Idempotencia
La creacion de ordenes y refunds usa `Idempotency-Key` y fingerprint interno. Reintentos con el mismo fingerprint retornan el recurso existente; fingerprints diferentes con la misma clave devuelven conflicto. Las claves y fingerprints son internos y no se exponen en respuestas de pago.

## Politicas de reserva
La politica vive en `ProfessionalProfile` porque el catalogo aun no tiene entidad `Service` independiente:
- `no_payment`: reserva funciona sin orden automatica.
- `pay_before_confirmation`: reserva queda `pending_payment`, bloquea slot y se confirma solo al aprobar pago.
- `pay_after_confirmation`: reserva se confirma al crearla y el pago queda pendiente sin bloquear la confirmacion inicial.

## Checkout fake
El checkout fake es autenticado, solo para cliente propietario y solo cuando `provider=fake`. No acepta montos, estados arbitrarios ni datos de tarjeta.

## Confirmacion y cancelacion
La aprobacion confirma una reserva `pending_payment` una sola vez reutilizando el flujo existente de confirmacion. Rechazo y expiracion cancelan solo reservas `pending_payment`. `pay_after_confirmation` no cancela automaticamente por rechazo en esta etapa.

## Sync, retry y reconcile
Admin puede sincronizar provider, reintentar operaciones manuales y reconciliar ordenes/refunds. Reconcile corrige estados seguros, detecta inconsistencias y no reabre reservas canceladas.

## Reembolsos
Admin puede solicitar refunds totales o parciales sobre ordenes `approved`. Provider fake y Mercado Pago estan soportados. Refund no modifica estado de reserva y actualiza solo el resumen de pago.

## Permisos
Admin administra pagos, providers, sync/retry/reconcile y refunds. Profesional y cliente solo leen pagos/refunds propios. Checkout cliente valida propiedad. No hay checkout anonimo en el MVP.

## Eventos
Eventos operativos minimos: `payment.order.created`, `payment.approved`, `payment.rejected`, `payment.expired`, `payment.refund.requested`, `payment.refund.approved`, `payment.refund.rejected`, `payment.refund.failed`. Los payloads son minimos y sanitizados.

## Endpoints principales
- Admin: `/api/v1/admin/payment-orders`, `/submit`, `/cancel`, `/sync-provider`, `/reconcile`, `/fake/*`.
- Admin refunds: `/api/v1/admin/payment-orders/{id}/refunds`, `/api/v1/admin/payment-refunds/{id}/submit`, `/sync-provider`, `/retry`, `/reconcile`, `/fake/*`.
- Cliente: `/api/v1/clients/me/payment-orders`, `/checkout`, `/checkout/approve`, `/checkout/reject`, `/refunds`.
- Profesional: `/api/v1/professionals/me/payment-orders`, `/refunds`.
- Webhook: `/api/v1/webhooks/mercado-pago`.

## Pruebas
La validacion del modulo usa pruebas acotadas:
- `tests/test_payment_foundation.py`
- `tests/test_payment_checkout_policies.py`
- `tests/test_mercado_pago_checkout_pro.py`
- `tests/test_payment_refunds.py`

## Limitaciones
No hay produccion real de pagos, Checkout API, Brick, Webpay, Stripe funcional, chargebacks completos, facturacion, boletas, impuestos, conciliacion bancaria, workers, scheduler, colas ni retries automaticos. Mercado Pago queda preparado con sandbox/configuracion controlada.

## Estado final
Modulo 17 queda funcionalmente cerrado para el MVP. Cumple dominio de pagos, politicas de reserva, checkout fake, Checkout Pro, webhook firmado, idempotencia, sync/reconcile manual, refunds, permisos por rol, frontend compilable y migraciones en head.
