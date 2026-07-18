# RealMeet - Submodulo 17.4: refunds y conciliacion manual

## Objetivo
Agregar reembolsos total/parciales y conciliacion manual sobre ordenes de pago aprobadas, sin cambiar estados de reserva ni implementar devoluciones avanzadas, impuestos, facturacion o conciliacion bancaria.

## Modelo
Se agregan `PaymentRefund` y `PaymentRefundStatusHistory`. `PaymentOrder` mantiene un resumen con `refunded_amount`, `refund_status`, `last_refunded_at` y `refundable_amount` calculado.

## Estados
Refund usa `requested`, `processing`, `approved`, `rejected`, `cancelled`, `failed` y `reconcile_required`. La orden puede quedar `approved` con reembolso parcial o `refunded` cuando la suma aprobada cubre todo el monto pagado.

## Motivos
Los motivos permitidos son `appointment_cancelled`, `duplicate_payment`, `service_not_delivered`, `client_request`, `professional_request`, `administrative_adjustment` y `other`. `other` requiere resumen breve.

## Total y parcial
Admin puede solicitar reembolsos total o parciales. La suma de reembolsos aprobados no puede superar el monto pagado. CLP exige montos enteros positivos.

## Providers
`fake` permite aprobar, rechazar y fallar desde backoffice. Mercado Pago usa `POST /v1/payments/{payment_id}/refunds` con `X-Idempotency-Key` y consulta `GET /v1/payments/{payment_id}/refunds/{refund_id}`. En pruebas se usa cliente fake, no red real.

## Idempotencia
La creacion usa `Idempotency-Key` y fingerprint del monto, moneda, orden y motivo. Misma clave con fingerprint distinto retorna `payment_refund_idempotency_conflict`. Submit, sync, retry y reconcile son idempotentes por estado y `external_refund_id`.

## Reintentos
Retry aplica a refunds `failed` o `reconcile_required`. Si ya existe `external_refund_id`, retry sincroniza provider; no crea otro reembolso externo.

## Reconciliacion
Admin puede reconciliar un refund puntual y tambien la orden. Corrige resumen seguro de la orden cuando los refunds aprobados estan desincronizados. Si la suma excede el pago, retorna inconsistencia para revision manual.

## Reservas
Los refunds no modifican el estado de la reserva. Si una reserva fue cancelada, no se reactiva por refund ni por reconcile.

## Permisos
Admin crea, procesa, sincroniza, reintenta, simula y reconcilia. Cliente y profesional solo leen refunds asociados a sus propias ordenes.

## Eventos
Se registran eventos operativos sanitizados en `AuditLog`: `payment.refund.requested`, `payment.refund.approved`, `payment.refund.rejected` y `payment.refund.failed`. No incluyen idempotency keys, fingerprints, secretos ni payloads provider completos.

## Webhooks Mercado Pago
En 17.4 los webhooks identificados como refund se registran e ignoran con `mercado_pago_refund_sync_required`; la fuente de verdad operativa es sync/reconcile manual.

## Frontend
Backoffice de Pagos muestra resumen de reembolso por orden y panel para solicitar/procesar/sincronizar/reconciliar. Cliente y profesional ven estado y monto reembolsado en su listado de pagos.

## Pruebas
La suite especifica cubre creacion, idempotencia, montos invalidos, parcial/total, fake, Mercado Pago con cliente fake, permisos, eventos sanitizados, reconcile y separacion de reservas.

## Limitaciones
No hay scheduler, refunds automaticos por cancelacion, webhooks reales de refund aplicando estado, chargebacks, retries automaticos, reembolsos anonimos, facturacion ni proveedores adicionales.
