# Submodulo 17.1 - Fundacion de pagos

## Objetivo

Crear una base provider-agnostic para ordenes de pago internas, operable por backoffice y consultable por profesionales y clientes.

## Dominio

`PaymentOrder` representa la intencion de cobro de RealMeet. Puede asociarse a una reserva o existir sin reserva para pruebas administrativas. La transaccion externa vive en el provider y solo se resume mediante `external_payment_id`, estado y referencias sanitizadas.

## Modelos

- `PaymentOrder`: reserva opcional, cliente, profesional, especialidad, provider, idempotencia, fingerprint, monto, moneda, estado y fechas relevantes.
- `PaymentOrderStatusHistory`: historial inmutable de transiciones con motivo, actor y referencia resumida del provider.

No existe modelo `Service` en el catalogo actual. Cuando hay reserva, el monto se deriva del precio del `ProfessionalProfile` y queda como snapshot. Si no hay precio o no hay reserva, el admin puede indicar monto manual.

## Estados

Estados: `draft`, `pending`, `requires_action`, `approved`, `rejected`, `cancelled`, `expired`, `failed`, `refunded`.

`refunded` queda catalogado, sin flujo funcional en 17.1.

## Provider Fake

`FakePaymentProvider` permite crear pagos pendientes, cancelar, consultar y hacer health check sin llamadas HTTP ni credenciales. Las simulaciones administrativas cubren aprobacion, rechazo, expiracion y fallo.

## Idempotencia

La creacion acepta `Idempotency-Key`. Misma clave y mismo payload retorna la orden existente; misma clave con payload distinto responde conflicto. Para reservas se genera una clave interna estable durante intentos activos.

## Transiciones

Las reglas viven en `app/payments/transitions.py`. Una orden final no se reabre; un nuevo intento crea otra orden cuando la anterior fue rechazada, cancelada, expirada o fallida. Una orden aprobada bloquea nuevos cobros en 17.1.

## Reserva

La orden valida reserva, cliente y profesional. En 17.1 los cambios de pago no modifican estados de reserva.

## Permisos

- Admin crea, lista, filtra, consulta historial, submitea, cancela, simula fake y consulta health.
- Profesional solo lee ordenes de sus reservas.
- Cliente solo lee ordenes propias.

## Seguridad

No se modelan numero de tarjeta, CVV, fecha de expiracion, nombre impreso, tokens de tarjeta ni secretos. Las respuestas cliente/profesional no exponen fingerprint, idempotencia ni referencias internas.

## Fuera de Alcance

Checkout publico, Mercado Pago real, Stripe real, tarjetas, webhooks de pago, confirmacion automatica de reserva, expiracion automatica, scheduler, reembolsos funcionales, impuestos, descuentos, facturacion y conciliacion.

## Pruebas

`backend/tests/test_payment_foundation.py` cubre creacion, validacion CLP, provider fake, provider no implementado, transiciones, historial, idempotencia, snapshot, orden activa, aislamiento por rol, seguridad de schemas y health check.

## Resultado

17.1 deja una fundacion de pagos usable para backoffice y visible para actores, sin procesamiento real de tarjetas y sin cambiar politicas de reserva.

## Limitaciones

El flujo no cobra dinero real. El checkout fake y la confirmacion condicionada por pago quedan para 17.2.
