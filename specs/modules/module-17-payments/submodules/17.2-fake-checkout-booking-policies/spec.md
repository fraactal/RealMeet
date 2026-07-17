# Submodulo 17.2 - Checkout fake y politicas de reserva

## Objetivo

Implementar un checkout fake autenticado para clientes y conectar las ordenes de pago con la confirmacion o cancelacion de reservas segun politica. No se procesan pagos reales ni datos de tarjeta.

## Politicas

No existe una tabla `Service` independiente en el catalogo actual. La politica de pago se incorpora al `ProfessionalProfile`, que hoy representa el servicio reservable del profesional.

- `no_payment`: conserva el flujo previo, crea reservas `pending` y no genera orden automatica.
- `pay_before_confirmation`: crea reserva `pending_payment`, genera una orden fake y confirma solo al aprobarse el pago.
- `pay_after_confirmation`: crea reserva `confirmed`, genera una orden fake y no bloquea la confirmacion inicial por pago.

Los servicios existentes migran con `no_payment`. Los montos son snapshot en `PaymentOrder`, moneda inicial `CLP`, expiracion por defecto 30 minutos y rango permitido 5-1440.

## Estados de reserva

Se agrega `pending_payment` porque `pending` ya representa el flujo normal sin pago. `pending_payment` bloquea el slot igual que `pending` y `confirmed`. Al expirar o rechazarse el pago, la reserva pasa a `cancelled` y libera disponibilidad.

## Checkout

El cliente autenticado accede a:

- `GET /api/v1/clients/me/payment-orders/{payment_order_id}/checkout`
- `POST /api/v1/clients/me/payment-orders/{payment_order_id}/checkout/approve`
- `POST /api/v1/clients/me/payment-orders/{payment_order_id}/checkout/reject`

El checkout valida propiedad, estado activo y `provider=fake`. No acepta importe, estado arbitrario, tarjetas, idempotency keys ni payloads internos desde frontend.

## Aprobacion

La aprobacion valida transicion, marca la orden como `approved`, registra historial, define `paid_at`, emite `payment.approved` y aplica la politica:

- `pay_before_confirmation`: `pending_payment -> confirmed`.
- `pay_after_confirmation`: la reserva permanece `confirmed`.

La operacion es idempotente. Los efectos posteriores de confirmacion reutilizan el servicio de reservas para no duplicar reuniones, notificaciones ni calendario.

## Rechazo

El rechazo marca la orden como `rejected`, registra historial y emite `payment.rejected`. Si la reserva esta `pending_payment`, pasa a `cancelled`. En `pay_after_confirmation` no se cancela automaticamente.

## Expiracion

No hay scheduler en 17.2. La expiracion se aplica al consultar checkout, aprobar, usar la accion admin fake o llamar el servicio reutilizable. Ordenes `pending` o `requires_action` pueden pasar a `expired`; finales no se reabren. Si la reserva esta `pending_payment`, pasa a `cancelled`.

## Idempotencia

Se reutilizan idempotency key y fingerprint de 17.1 para creacion de ordenes. La creacion automatica usa una clave estable por reserva. Aprobar, rechazar y expirar son idempotentes y evitan transiciones repetidas.

## Efectos posteriores

La confirmacion por pago llama el flujo central de confirmacion de reservas. En fallos parciales, la orden aprobada se conserva y la accion admin de reconciliacion puede corregir estados seguros.

## Reconciliacion

Admin puede llamar:

- `POST /api/v1/admin/payment-orders/{payment_order_id}/reconcile`

Resultados: `in_sync`, `appointment_confirmation_required`, `appointment_cancellation_required`, `payment_not_final` o `manual_review_required`. Corrige de forma segura orden aprobada con reserva pendiente, y orden rechazada/expirada con reserva pendiente de pago. No reactiva reservas canceladas.

## Permisos

Cliente: ver sus pagos, abrir checkout fake, aprobar o rechazar simuladamente sus ordenes fake.

Profesional: lectura de estado de pago, monto y expiracion asociados a sus reservas.

Admin: configurar politica en profesionales, simular estados fake, ver relacion reserva-pago y reconciliar.

## Fuera de alcance

Mercado Pago, Stripe, Webpay, PayPal, tarjetas, tokenizacion, checkout publico anonimo, webhooks reales, scheduler, workers, retries automaticos, reembolsos, impuestos, descuentos, cupones, boletas, facturas, suscripciones, conciliacion bancaria, despliegue y 17.3.

## Pruebas

`backend/tests/test_payment_checkout_policies.py` cubre default `no_payment`, flujos `pay_before_confirmation` y `pay_after_confirmation`, bloqueo/liberacion de slots, checkout propietario, provider fake, idempotencia, expiracion, reconciliacion, sanitizacion y validaciones administrativas.

## Resultado

17.2 deja pagos fake usables end-to-end desde cliente, administrables desde backoffice y visibles para profesionales sin exponer datos sensibles ni introducir providers reales.

## Limitaciones

La politica vive temporalmente en `ProfessionalProfile` hasta que exista un modelo `Service`. No se reactiva una reserva cancelada por pago fallido o vencido; el cliente debe crear una nueva reserva si el slot sigue disponible.
