# Submodule 13.2 - WhatsApp Cloud Provider

## Objective

Implement controlled administrative sending of WhatsApp template messages through WhatsApp Cloud API while keeping reservations and reminders disconnected.

## Scope

- Outbound `WhatsAppMessage` persistence.
- Typed WhatsApp Cloud client contract.
- HTTP client for Meta Graph API.
- Fake client for tests.
- Token resolution from environment variable references.
- Consent, recipient and template validation.
- Template sync read-only from Meta.
- Manual admin send endpoint and retry endpoint.
- Health check read-only.
- Webhook status correlation for outbound messages.
- Admin backoffice controls.

## Out Of Scope

- Automatic reservation notifications.
- Reminders, fallback email, workers, queues, bulk messages, free-form messages, replies, chatbot, AI, multimedia and marketing.
- Real Meta calls during automated validation.

## Architecture

- `WhatsAppCloudClient`: builds and normalizes Graph API requests.
- `WhatsAppMessagingService`: validates integration, token, consent, template, variables and idempotency; persists messages and executions.
- `WhatsAppWebhookService`: keeps webhook event persistence and correlates status events to outbound messages.
- Admin routers: authorization and schema translation only.

## Client

The real client derives URLs from integration configuration:

```text
https://graph.facebook.com/{graph_api_version}/{phone_number_id}/messages
```

Frontend never supplies Graph URL, headers, token, Graph version or Phone Number ID for send operations.

## Authentication

The access token is resolved from the configured `secret_references.access_token` environment variable name and stays in memory for the outbound request only.

## Templates

Only local `utility` templates with status `approved` can be sent. Sync is read-only and updates local rows by name and language.

## Recipients And Consent

13.2 accepts an existing consent ID for real sends. The service verifies user, purpose, granted status and HMAC. No free phone number is accepted for real sending.

## Idempotency

Unique key: `(integration_id, idempotency_key)`.

- Accepted/sent/delivered/read: return already processed and do not call client.
- Queued: conflict/in-progress.
- Failed: reuse row and increment attempt on retry/manual resend.

## Message State

Allowed states:

- `queued`
- `accepted`
- `sent`
- `delivered`
- `read`
- `failed`
- `cancelled`
- `skipped`

The POST response marks `accepted`, not delivered.

## Webhooks

Status webhooks update local messages monotonically. Unknown external message IDs do not create outbound message rows.

## Errors And Rate Limits

Provider errors are normalized to internal codes. Rate limit responses mark the message failed and allow manual retry later. No automatic retry loop is added.

## Security

No full phone numbers, variables, rendered content, request bodies, response bodies, headers or tokens are stored or returned.

## Tests

Tests use the fake client only. No Meta calls are made during automated validation.

## Debt For 13.3

- Connect reservations and reminders.
- Add queues/workers and operational retry policies.
- Add fallback email.
- Add delivery reconciliation dashboards.
