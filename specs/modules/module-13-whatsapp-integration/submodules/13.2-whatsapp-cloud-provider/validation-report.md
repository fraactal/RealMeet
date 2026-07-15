# Validation Report

Status: completed.

## Planned Commands

```bash
docker-compose exec -T backend alembic upgrade head
docker-compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py tests/test_google_oauth_foundation.py tests/test_google_meet_provider.py tests/test_appointment_meeting_provisioning.py tests/test_whatsapp_domain_consent.py tests/test_whatsapp_webhooks.py tests/test_whatsapp_cloud_provider.py -ra
docker-compose exec -T frontend npm run build
docker-compose exec -T backend alembic current
docker-compose ps
```

Health:

- `/health`
- `/ready`

## Results

- `docker-compose exec -T backend alembic upgrade head`: passed, upgraded `20260715_0009 -> 20260715_0010`.
- `docker-compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py tests/test_google_oauth_foundation.py tests/test_google_meet_provider.py tests/test_appointment_meeting_provisioning.py tests/test_whatsapp_domain_consent.py tests/test_whatsapp_webhooks.py tests/test_whatsapp_cloud_provider.py -ra`: passed, `81 passed, 1 warning`.
- `docker-compose exec -T frontend npm run build`: passed. Vite reported existing chunk-size warning.
- `docker-compose exec -T backend alembic current`: `20260715_0010 (head)`.
- `docker-compose ps`: backend, db and frontend healthy.
- `/health`: `status=ok`, `environment=docker`.
- `/ready`: `status=ready`, `database=ok`, `configuration=ok`.

## Secret Scan

Command included WhatsApp, token, bearer, secret and password terms across backend, frontend, specs, README and env examples. Findings are limited to:

- Empty env placeholders.
- Environment variable names.
- Existing demo credentials.
- Fake test values such as `fake-token`, `Secret123!`, `APP_SECRET_TEST`.
- Code identifiers and documentation.

No real WhatsApp, Meta or Google credentials were added.

## Manual Fake Validation

Automated fake validation covers:

- Fake health and template sync.
- Fake template send accepted.
- Idempotency duplicate skip.
- Failed message reuse with incremented attempt.
- Webhook sent/delivered/read monotonic update.
- Unknown webhook message ID ignored.
- Admin API role protection and safe response.

## Screenshot Attempt

Screenshot generation was attempted with Edge headless. It produced no PNG files in this local session, consistent with the browser/runtime failure observed in 13.1C. This is documented as an environment limitation and does not block closure because build and functional validation passed.

## Real Manual Validation Later

Do not execute automatically. For a real controlled send:

1. Configure real WABA and Phone Number ID.
2. Configure token only in environment.
3. Register and verify public webhook.
4. Sync templates.
5. Confirm a `utility` template is approved.
6. Create or select an authorized test user.
7. Register explicit consent.
8. Send manually from admin backoffice.
9. Verify webhooks update message status.
