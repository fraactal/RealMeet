# Modulo 17 - Pagos

## Roadmap

17.1 Fundacion de pagos: ordenes internas de cobro, provider fake, estados, historial, idempotencia, APIs y frontend acotado.

17.2 Checkout y politicas de reserva: reserva pendiente de pago, checkout fake, expiracion controlada y cancelacion por falta de pago.

17.3 Proveedor de pago real: integracion a definir entre Mercado Pago y Stripe.

17.4 Reembolsos y conciliacion: reembolso manual, retry, reconcile y estados inconsistentes.

17.5 Cierre liviano: validacion integrada y documentacion de limites operativos.

## Decisiones 17.1

- `PaymentOrder` es la intencion interna de cobro y no almacena datos de tarjeta.
- El provider queda detras de contratos agnosticos.
- `fake` es el unico provider implementado.
- `mercado_pago` y `stripe` quedan registrados pero no implementados.
- No existe tabla de servicios en el catalogo actual; la orden usa snapshot del precio del profesional cuando hay reserva y permite monto manual administrativo cuando corresponde.
- La aprobacion de pago no confirma reservas en 17.1.
- La expiracion o rechazo de pago no cancela reservas en 17.1.
