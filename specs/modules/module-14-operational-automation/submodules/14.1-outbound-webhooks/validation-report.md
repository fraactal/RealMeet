# Reporte De Validacion 14.1

## Comandos

- `docker-compose exec -T backend alembic upgrade head`: passed; aplico `20260715_0012`.
- `docker-compose exec -T backend pytest -q tests/test_outbound_webhooks.py -ra`: passed, `8 passed, 1 warning`.
- `docker-compose exec -T frontend npm run build`: passed; warning conocido de chunk > 500 kB.
- `docker-compose exec -T backend alembic current`: `20260715_0012 (head)`.
- `docker-compose ps`: backend, db y frontend healthy.
- `GET /health`: `status=ok`, `environment=docker`.
- `GET /ready`: `status=ready`, `database=ok`, `configuration=ok`.

## Cobertura

- Crear suscripcion valida.
- URL insegura rechazada.
- Secreto directo rechazado.
- Firma HMAC estable.
- Idempotencia por suscripcion y evento.
- Entrega fake exitosa.
- Entrega fake fallida.
- Retry manual.
- `appointment.created` genera entrega.
- Fallo webhook no corrompe el contexto de reserva.
- `appointment.cancelled` genera entrega.
- Cliente/profesional reciben 403.
- Admin permitido.

## Warning

El unico warning corresponde a `passlib` usando `crypt`, deprecado para Python 3.13. No se actualizan dependencias en 14.1.

## Resultado

Submodulo 14.1 validado con pruebas acotadas y build frontend. No se ejecuto suite backend completa, no se hizo push y no se implemento n8n real.
