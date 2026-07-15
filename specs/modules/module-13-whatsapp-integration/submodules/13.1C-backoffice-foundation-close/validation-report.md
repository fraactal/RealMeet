# Validation Report

Status: completed with screenshot limitation.

## Planned Commands

```bash
docker-compose exec -T backend alembic upgrade head
docker-compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py tests/test_google_oauth_foundation.py tests/test_google_meet_provider.py tests/test_appointment_meeting_provisioning.py tests/test_whatsapp_domain_consent.py tests/test_whatsapp_webhooks.py -ra
docker-compose exec -T frontend npm run build
docker-compose exec -T backend alembic current
docker-compose ps
```

Health:

- `/health`
- `/ready`

## Results

- `docker-compose exec -T backend alembic upgrade head`: passed.
- `docker-compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py tests/test_google_oauth_foundation.py tests/test_google_meet_provider.py tests/test_appointment_meeting_provisioning.py tests/test_whatsapp_domain_consent.py tests/test_whatsapp_webhooks.py -ra`: passed, `74 passed, 1 warning`.
- `docker-compose exec -T frontend npm run build`: passed. Vite reported the existing chunk-size warning above 500 kB.
- `docker-compose exec -T backend alembic current`: `20260715_0009 (head)`.
- `docker-compose ps`: backend, db and frontend healthy.
- `/health`: `status=ok`, `environment=docker`.
- `/ready`: `status=ready`, `database=ok`, `configuration=ok`.

## Role Validation

- No session requesting `/api/v1/admin/integrations`: `401`.
- Client requesting `/api/v1/admin/integrations`: `403`.
- Professional requesting `/api/v1/admin/integrations`: `403`.
- Frontend navigation keeps `Integraciones` restricted to `roles: ["admin"]`.

## Local Validation Data

- Created integration: `WhatsApp foundation 13.1C`, ID `646`.
- Created local template: `appointment_confirmation_13_1c`, ID `7`.
- Local validation result: `whatsapp_local_config_valid`.
- Consent correction was not created because the local runtime does not configure `WHATSAPP_PHONE_HMAC_KEY`; this is expected security behavior for private phone correlation.

## Screenshot Attempt

Screenshots could not be generated in this session. The in-app browser runtime failed to initialize with `Cannot redefine property: process`, and Microsoft Edge headless failed with GPU/renderer errors or produced no screenshot files. A temporary local session bridge file was created only for the attempt and removed before commit.

Missing screenshots are an environment limitation, not a build or application failure.
