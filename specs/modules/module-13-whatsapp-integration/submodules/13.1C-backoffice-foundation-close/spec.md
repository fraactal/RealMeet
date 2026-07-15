# Submodule 13.1C - WhatsApp backoffice and foundation close

## Objective

Expose the WhatsApp foundation from 13.1A and 13.1B in the existing admin integrations backoffice and close Module 13.1 documentation.

## Scope

- Extend `/dashboard/admin/integrations` with WhatsApp-specific configuration, status, templates, consent summaries and webhook event review.
- Reuse existing admin guard, integrations page, UI primitives and TanStack Query.
- Add frontend types, API functions and labels for WhatsApp domain objects.
- Validate responsive and accessible behavior.
- Run integrated backend tests and frontend build.
- Produce final 13.1 report.

## Out of Scope

- Sending WhatsApp messages.
- Meta Graph API calls.
- Template sync with Meta.
- Chatbot, replies, conversations, media, reminders, fallback email, workers, retries and automatic retention.
- Reservation changes.
- Push, merge or deployment.

## Route

The UI remains inside:

```text
/dashboard/admin/integrations
```

No new productive navigation entry is needed because the admin integration section already exists.

## Components

- WhatsApp foundation panel inside the selected integration detail.
- WhatsApp configuration fields inside the existing integration form.
- Capability summary cards.
- Webhook status panel with public URL copy action.
- Webhook event list and detail modal.
- Local template list and form modal.
- Consent summary list and admin correction modal.

## API Used

- Admin integration CRUD already present.
- `POST /api/v1/admin/integrations/{id}/whatsapp/validate`
- `GET /api/v1/admin/integrations/{id}/whatsapp/status`
- `GET /api/v1/admin/integrations/{id}/whatsapp/webhook-status`
- `GET /api/v1/admin/integrations/{id}/whatsapp/webhook-events`
- `GET /api/v1/admin/integrations/{id}/whatsapp/webhook-events/{event_id}`
- `GET/POST/PATCH /api/v1/admin/integrations/{id}/whatsapp/templates`
- `GET /api/v1/admin/whatsapp/consents`
- `POST /api/v1/admin/whatsapp/consents/corrections`

## Roles

Admin only. Client, professional and unauthenticated users rely on existing route and backend guards.

## Security

The UI does not expose tokens, verify tokens, app secrets, signatures, hashes, full phone numbers, webhook bodies or message text. It does not enable sending or real provider tests.

## Responsive and Accessibility

Use mobile cards, single-column forms, accessible labels, Escape-close modals and clear disabled/empty/loading states.

## Debt for 13.2

Real provider client, sending, outgoing message model, Meta template sync, delivery correlation and reservation/notification integration.
