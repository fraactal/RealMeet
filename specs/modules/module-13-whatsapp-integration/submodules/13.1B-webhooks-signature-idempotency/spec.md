# Submodule 13.1B - WhatsApp webhooks, signature and idempotency

## Objective

Receive WhatsApp Cloud webhook verification and events safely, without sending messages, calling Meta, modifying appointments, or adding frontend UI.

## Scope

- Public GET verification endpoint.
- Public POST webhook endpoint with raw-body HMAC validation.
- Configurable body-size limit.
- Safe event extraction, classification and persistence.
- Idempotency by stable event key.
- Admin backend APIs for webhook event listing, detail and status.
- Tests with fake payloads and fake signatures only.

## Out of Scope

- Backoffice frontend, outgoing messages, Graph API calls, template sync, media downloads, conversations, chatbot, appointment actions, reminders, retries, workers, cleanup jobs, n8n, Twilio, push and deployment.

## Endpoints

- `GET /api/v1/integrations/whatsapp/webhook`
- `POST /api/v1/integrations/whatsapp/webhook`
- `GET /api/v1/admin/integrations/{integration_id}/whatsapp/webhook-events`
- `GET /api/v1/admin/integrations/{integration_id}/whatsapp/webhook-events/{event_id}`
- `GET /api/v1/admin/integrations/{integration_id}/whatsapp/webhook-status`

## GET Verification

The GET endpoint validates `hub.mode=subscribe`, compares `hub.verify_token` against `WHATSAPP_WEBHOOK_VERIFY_TOKEN` with constant-time comparison, and returns `hub.challenge` as plain text on success.

Failure behavior:

- Missing config: `503`.
- Malformed request: `400`.
- Invalid token: `403`.

## POST Authenticity

The POST endpoint reads raw bytes once, rejects bodies above `WHATSAPP_WEBHOOK_MAX_BODY_BYTES`, validates `X-Hub-Signature-256: sha256=<digest>` when required, and only then parses JSON.

Signature can be disabled only through `WHATSAPP_WEBHOOK_REQUIRE_SIGNATURE=false`, intended for explicit local/test use.

## Event Model

`WhatsAppWebhookEvent` stores only reduced metadata:

- event key;
- payload hash;
- event type;
- processing status;
- external message ID;
- masked/hashed phone number ID;
- optional sender/recipient hashes;
- timestamps;
- safe metadata;
- summarized error code/message.

It never stores the raw body, message text, headers, signatures, contact names, full phones or media.

## Classification

Supported initial event types:

- `inbound_message`;
- `message_sent`;
- `message_delivered`;
- `message_read`;
- `message_failed`;
- `template_status`;
- `unknown`.

## Idempotency

One row is kept per `event_key`. Repeated events increment `received_count`, update `last_received_at`, set `duplicate=true`, and return success without creating a second row.

Event keys:

- inbound: `message:<external_message_id>`;
- status: `status:<external_message_id>:<status>:<timestamp>`;
- unknown: hash of stable reduced fields.

## HTTP Strategy

- Valid event: `200`.
- Duplicate: `200`.
- Unknown authenticated event: `200`.
- Unknown integration with valid signature: `200`, persisted without association.
- Invalid signature: `403`.
- Missing required signature: `401`.
- Invalid JSON or empty body: `400`.
- Oversized body: `413`.
- Temporary persistence failure: `500`.

## Privacy

The service hashes phone identifiers with the 13.1A HMAC helper when a real phone-like value is present and masks phone number IDs. Admin APIs return partial event keys and message IDs, not full body or full hashes.

## Rate Limiting

The existing in-memory limiter is route-specific for login and appointment creation. 13.1B does not add webhook rate limiting because reverse-proxy trust is not defined yet. Signature, size limit and idempotency are the primary protections.

## Retention

`WHATSAPP_WEBHOOK_EVENT_RETENTION_DAYS` is added for future cleanup planning. No cleanup job is implemented in 13.1B.

## Debt for 13.1C

- Admin frontend for webhook status and event review.
- Responsive and accessibility validation.

## Debt for 13.2

- `WhatsAppMessage` outbound model.
- Real send provider.
- Delivery-state correlation with outgoing messages.
- Retry and fallback policy.
