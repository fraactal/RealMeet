# Validation Report

Status: completed.

## Commands

Planned:

```bash
docker compose exec -T backend alembic upgrade head
docker compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py tests/test_google_oauth_foundation.py tests/test_google_meet_provider.py tests/test_appointment_meeting_provisioning.py tests/test_whatsapp_domain_consent.py -ra
docker compose exec -T backend alembic current
docker compose ps
```

Health checks:

- `/health`
- `/ready`

## Manual API Validation

Covered with API-level tests using `TestClient` and local database records:

- User consent grant/read/revoke.
- Admin WhatsApp local validation/status.
- Admin local template creation/update and sensitive-variable rejection.
- Admin safe consent summary and correction.
- Professional blocked from admin routes.

## Results

- `docker-compose exec -T backend alembic upgrade head`: passed after migration enum definitions were adjusted to use existing created types for table columns.
- `docker-compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py tests/test_google_oauth_foundation.py tests/test_google_meet_provider.py tests/test_appointment_meeting_provisioning.py tests/test_whatsapp_domain_consent.py -ra`: `67 passed, 1 warning`.
- Warning: existing `passlib` crypt deprecation warning.
- `docker-compose exec -T backend alembic current`: `20260715_0008 (head)`.
- `docker-compose ps`: backend, db and frontend healthy.
- `/health`: `{"status":"ok","environment":"docker"}`.
- `/ready`: `{"status":"ready","database":"ok","configuration":"ok"}`.
- `git diff --check`: no whitespace errors; CRLF normalization warnings only.
- Secret scan: no real WhatsApp/Meta token found; only `do-not-store` test input used to assert rejection.
