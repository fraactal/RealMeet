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

## Decisiones 17.2

- La politica de pago se agrega en `ProfessionalProfile` porque aun no existe tabla `Service`.
- Servicios existentes quedan en `no_payment` y mantienen el flujo previo.
- Se agrega `pending_payment` para diferenciar una reserva que bloquea slot mientras espera pago.
- `pay_before_confirmation` confirma reservas solo al aprobar una orden fake.
- `pay_after_confirmation` confirma la reserva al crearla y mantiene el pago como pendiente.
- Rechazo o expiracion cancelan solo reservas `pending_payment`.
- No se reactiva una reserva cancelada por pago rechazado o expirado.
- El checkout cliente es autenticado, solo `provider=fake` y no acepta datos de tarjeta.
