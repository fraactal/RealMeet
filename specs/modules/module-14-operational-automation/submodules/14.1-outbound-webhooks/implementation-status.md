# Estado De Implementacion 14.1

Estado: implementado.

## Decisiones

- Se crea paquete backend `app.automation` para aislar contratos, cliente y servicio.
- Las suscripciones quedan deshabilitadas por defecto.
- `generic_webhook` y `n8n` comparten la misma base, sin flujos especificos n8n.
- La entrega fallida se reintenta manualmente reutilizando la misma fila.
- Los eventos de reserva se publican despues del commit y no bloquean la reserva.

## Implementado

- Modelos `WebhookSubscription` y `WebhookDelivery`.
- Migracion `20260715_0012`.
- Contratos `DomainEvent` versionados.
- Catalogo inicial de eventos.
- Firma HMAC-SHA256.
- Cliente HTTP real y fake.
- Servicio `WebhookDeliveryService`.
- Publisher `DomainEventPublisher`.
- Emision inicial de `appointment.created` y `appointment.cancelled`.
- API admin solicitada.
- Backoffice minimo dentro de Integraciones.
- Pruebas acotadas `tests/test_outbound_webhooks.py`.

## Limitaciones

- n8n queda solo como contenedor administrativo; no hay workflows reales.
- No hay retries automaticos, workers, colas ni DLQ.
- El retry manual reconstruye un payload seguro reducido para no persistir cuerpos completos.
- No se ejecuta suite backend completa por criterio SDD liviano del modulo.
