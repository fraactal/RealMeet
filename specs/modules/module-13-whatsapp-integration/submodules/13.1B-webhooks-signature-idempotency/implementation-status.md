# Implementation Status

Status: implemented.

## Initial Verification

- Branch: `codex/module-13-whatsapp-integration`.
- HEAD: `e1165d6 feat(integrations): add WhatsApp domain and consent`.
- Working tree: clean before 13.1B changes.

## Investigation

- `backend/app/api/router.py`: public routers are mounted under `/api/v1`; a new unguarded router is needed for `/integrations/whatsapp/webhook`.
- `backend/app/core/middleware.py`: existing rate limit is route-specific and does not cover webhook routes.
- `backend/app/core/config.py`: WhatsApp settings from 13.1A exist; webhook settings will extend the same Pydantic settings class.
- `backend/app/whatsapp/configuration.py`: local config validates `phone_number_id`, used for integration resolution.
- `backend/app/whatsapp/phone.py`: HMAC helper is reused for phone-like identifiers.
- `backend/app/models/integration.py`: webhook events can nullable-FK to `integrations`.
- `backend/app/api/routes/admin.py`: admin WhatsApp routes already exist and can be extended.
- `backend/tests/test_whatsapp_domain_consent.py`: TestClient and cleanup patterns are available.

## Decisions

- `WhatsAppMessage` remains deferred to 13.2.
- No webhook rate limiter is added in 13.1B.
- Unknown but authenticated phone number IDs are accepted and persisted unassociated to avoid endless Meta retries.

## Completion Notes

- Added webhook settings and safe `.env.example` placeholders.
- Added `WhatsAppWebhookEvent` and migration `20260715_0009`.
- Added public `GET/POST /api/v1/integrations/whatsapp/webhook`.
- Added HMAC-SHA256 signature validation using raw body bytes.
- Added size limit, JSON validation and normalized HTTP errors.
- Added event extraction for inbound messages, delivery statuses, template status and unknown events.
- Added integration resolution by configured `phone_number_id`.
- Added idempotency with one row per `event_key`, `received_count` and `last_received_at`.
- Added admin event list/detail/status APIs.
- Added `tests/test_whatsapp_webhooks.py`.
- Updated README with webhook behavior, privacy, rate-limit and retention notes.
- No frontend, reservation or outgoing message code was added.
