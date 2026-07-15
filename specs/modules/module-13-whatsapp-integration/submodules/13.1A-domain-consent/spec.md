# Submodule 13.1A - WhatsApp domain, configuration and consent

## Objective

Prepare the backend domain foundation for WhatsApp Cloud API without sending messages, receiving webhooks, changing appointments, or adding frontend/backoffice UI.

## Scope

- Optional WhatsApp application settings with safe empty defaults.
- Local `whatsapp_cloud` integration configuration validation for `messaging`.
- Secret references only; no persisted token values.
- Central phone normalization, masking and keyed HMAC correlation.
- Explicit WhatsApp consent model, schemas, repository, service and APIs.
- Local WhatsApp template model, schemas, repository, service and admin APIs.
- Alembic migration after `20260715_0007`.
- Backend tests without network calls.

## Out of Scope

- Webhook GET/POST, signature verification and webhook event persistence.
- Real Meta API calls, template synchronization, message sending or retries.
- Appointment, reminder, email fallback, scheduler, worker or frontend changes.
- Marketing consent, campaigns, Twilio, n8n and deployment.

## Entities

- `WhatsAppConsent`: one current row per user, phone hash and transactional purpose. Revocation updates status and timestamps rather than deleting data.
- `WhatsAppTemplate`: local template definitions linked to a WhatsApp integration. New templates start as `draft`.
- `WhatsAppMessage`: deferred to 13.2 because no send/receive flow exists in 13.1A.

## Enums

- Consent status: `not_granted`, `granted`, `revoked`.
- Consent purpose: `appointment_transactional`, `appointment_reminders`, `appointment_updates`.
- Consent source: `self_service`, `admin_correction`, `imported`, `system_migration`.
- Template status: `draft`, `pending`, `approved`, `rejected`, `paused`, `disabled`, `unknown`.
- Template category: `utility`, `authentication`, `marketing`, `unknown`; 13.1A creation accepts only `utility`.
- Template purpose: `appointment_confirmation`, `appointment_reminder`, `appointment_updated`, `appointment_cancelled`, `meeting_ready`.

## Privacy

Phone numbers are normalized to E.164 for validation, stored on consent rows only when needed for the user's own consent record, masked for administrative output, and correlated with a keyed HMAC. Audit logs must not include full phone numbers, phone hashes, config payloads, tokens or secret values.

## Configuration

Settings are optional and safe by default:

- `WHATSAPP_CLOUD_ENABLED`
- `WHATSAPP_GRAPH_API_VERSION`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- `WHATSAPP_DEFAULT_LANGUAGE`
- `WHATSAPP_DEFAULT_COUNTRY_CODE`
- `WHATSAPP_PHONE_HMAC_KEY`

The backend must start when they are absent. Real credentials remain outside Git and outside integration config.

## Secret Strategy

13.1A stores only environment variable names. `Integration.secret_reference` remains available for the primary access-token reference and WhatsApp config can include `secret_references` containing uppercase environment variable references for access token, app secret, verify token and phone HMAC key. The recursive safe metadata validator rejects secret-looking values and sensitive keys outside the explicitly typed secret reference object.

## API

User consent:

- `GET /api/v1/users/me/whatsapp-consents`
- `POST /api/v1/users/me/whatsapp-consents`
- `DELETE /api/v1/users/me/whatsapp-consents/{purpose}`

Admin WhatsApp integration:

- `GET /api/v1/admin/integrations/{integration_id}/whatsapp/status`
- `POST /api/v1/admin/integrations/{integration_id}/whatsapp/validate`
- `GET /api/v1/admin/integrations/{integration_id}/whatsapp/templates`
- `POST /api/v1/admin/integrations/{integration_id}/whatsapp/templates`
- `GET /api/v1/admin/integrations/{integration_id}/whatsapp/templates/{template_id}`
- `PATCH /api/v1/admin/integrations/{integration_id}/whatsapp/templates/{template_id}`
- `GET /api/v1/admin/whatsapp/consents`
- `POST /api/v1/admin/whatsapp/consents/corrections`

## Security

- Admin routes use existing admin guard.
- User routes use authenticated current user only.
- Professional users have no administrative WhatsApp access.
- Schemas use `extra="forbid"` to block mass assignment.
- No network calls are made.
- No webhook endpoints are added.
- No secrets or full phones are logged or returned in admin summaries.

## Migration

Create revision `20260715_0008` with `whatsapp_consents` and `whatsapp_templates`, indexes, foreign keys and uniqueness constraints. Existing data is not modified and no automatic consent is granted.

## Debt for 13.1B

- Webhook verification endpoint.
- Raw body signature verification.
- Body-size limits.
- Webhook event persistence and idempotency.
- Delivery status classification.

## Debt for 13.1C

- Admin UI for WhatsApp configuration.
- Template and consent backoffice screens.
- Responsive and accessibility review.
