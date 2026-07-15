# Implementation Status

Status: implemented.

## Initial Verification

- Branch: `codex/module-13-whatsapp-integration`.
- HEAD: `ac88b79 feat(integrations): add WhatsApp foundation backoffice`.
- Working tree: clean before 13.2 changes.
- Migration `20260715_0009` present as `backend/alembic/versions/20260715_0009_whatsapp_webhook_events.py`.
- 13.1 foundation intact.

## Investigation

Relevant files:

- `backend/app/models/whatsapp.py`: `WhatsAppConsent`, `WhatsAppTemplate`, `WhatsAppWebhookEvent`.
- `backend/app/whatsapp/enums.py`: consent, template and webhook enums.
- `backend/app/whatsapp/configuration.py`: validated WhatsApp integration config and secret references.
- `backend/app/whatsapp/services.py`: consent, template and webhook services.
- `backend/app/whatsapp/repositories.py`: repositories for consent/template/webhook events.
- `backend/app/models/integration.py`: `Integration`, `IntegrationExecution`.
- `backend/app/services/integrations.py`: integration idempotency/execution patterns.
- `backend/app/api/routes/admin.py`: existing admin WhatsApp endpoints.
- `frontend/src/components/admin/integrations/WhatsAppFoundationPanel.tsx`: 13.1C backoffice extension point.
- `frontend/src/pages/AdminIntegrationsPage.tsx`: admin integrations page and query wiring.

## Decisions

- Use a small HTTP client; do not add a WhatsApp SDK.
- Keep 13.2 send admin-only and explicit.
- Use consent ID for recipient selection.
- Keep fake client injectable for tests, not exposed as a production UI option.
- Do not modify reservation services, schemas or UI.

## Completion Notes

- Added `WhatsAppMessage` ORM model and migration `20260715_0010`.
- Added `WhatsAppCloudClient` protocol, HTTP implementation and fake implementation.
- Added `WhatsAppMessagingService` for admin health, template sync, send, retry path support through idempotent resend, message listing and webhook correlation.
- Added admin endpoints for health check, template sync, messages, message detail and retry.
- Extended webhook processing to update outbound message state for known external message IDs.
- Extended frontend backoffice with health, sync, manual send form, message cards and retry action.
- Updated README, `.env.example`, `backend/.env.example` and traceability matrix.

## Backend Files

- `backend/app/whatsapp/cloud_client.py`
- `backend/app/whatsapp/messaging.py`
- `backend/app/models/whatsapp.py`
- `backend/app/whatsapp/enums.py`
- `backend/app/whatsapp/schemas.py`
- `backend/app/whatsapp/repositories.py`
- `backend/app/whatsapp/services.py`
- `backend/app/api/routes/admin.py`
- `backend/alembic/versions/20260715_0010_whatsapp_messages.py`
- `backend/tests/test_whatsapp_cloud_provider.py`

## Frontend Files

- `frontend/src/components/admin/integrations/WhatsAppFoundationPanel.tsx`
- `frontend/src/pages/AdminIntegrationsPage.tsx`
- `frontend/src/api/queries.ts`
- `frontend/src/types/index.ts`
- `frontend/src/utils/labels.ts`

## Security Notes

- No tokens are stored in database.
- Send payload rejects arbitrary token, phone number, provider, Graph URL and headers by schema.
- Recipient is selected by consent ID and returned masked.
- Variables are validated but not persisted.
- HTTP client derives URL from backend integration config.
- Tests use fake client only.

## Limitation

The retry endpoint cannot reconstruct variables without storing message content. The supported safe retry path is to resend through the admin form with the same idempotency key after a failed message; the failed row is reused and attempt is incremented.
