# Acceptance Criteria

- `/dashboard/admin/integrations` supports `whatsapp_cloud` creation/editing.
- WhatsApp is shown as foundation-ready but not operational for sending.
- Secret reference inputs explain that only environment variable names are allowed.
- Local validation uses the WhatsApp admin API and does not call Meta.
- Webhook status displays configuration booleans and public URL without secrets.
- Webhook event list/detail display only safe reduced data.
- Local templates can be listed, created and edited without free-form JSON as the primary UX.
- Consent summaries show masked phones only.
- Admin correction requires a reason, purpose, phone and explicit confirmation.
- Existing admin navigation remains unchanged except current integration content.
- No frontend route is exposed to client/professional users.
- Frontend build passes.
- Required backend tests pass.
- No messages are sent.
- No reservations are modified.
- A single commit is created with message `feat(integrations): add WhatsApp foundation backoffice`.
