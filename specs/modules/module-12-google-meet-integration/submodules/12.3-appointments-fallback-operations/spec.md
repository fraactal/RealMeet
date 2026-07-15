# Submodule 12.3 - Appointments, fallback, and admin operations

## Objective

Connect meeting provisioning to appointments through a controlled resolver that can choose Google Meet, mock fallback, or no automatic meeting according to a non-secret policy. Appointment booking must remain reliable even when meeting provisioning fails.

## Current appointment flow

- `AppointmentService.create` validates client, professional, availability, and overlaps.
- Today the mock meeting is created before the appointment row is flushed.
- The appointment persists `meeting_provider`, `meeting_url`, `external_meeting_id`, and `calendar_event_id`.
- If the configured meeting provider raises `NotImplementedError`, appointment creation fails with `503`.
- Confirmation and cancellation only update appointment status and send existing notifications.
- Confirmation email includes `appointment.meeting_url` when present and labels it as a demo meeting.
- APScheduler only has a reminder placeholder and does not create meetings.
- Client/professional/admin serializers expose meeting URL and simple active/inactive state.

## Scope

- Add explicit appointment meeting provisioning policy.
- Add a resolver/orchestrator for Google, mock, fallback, disabled, and required flows.
- Persist a one-to-one appointment meeting link with provisioning state and safe error summary.
- Provision meeting after appointment persistence.
- Sync cancellation best-effort after reservation cancellation.
- Add admin retry and reconciliation endpoints.
- Expose safe meeting state to client/professional/admin.
- Add compact UI updates for meeting state, policy config, and admin operations.

## Out of scope

- Background retries, Google webhooks, bidirectional sync, rescheduling, professional-specific Google accounts, calendars per professional, WhatsApp, n8n, Microsoft 365, payments, deployment, push, or merge.

## Provider policy

Policies are stored in the non-secret Google Meet integration config, with code defaults when no integration exists:

- `mock_only`: always create a mock meeting.
- `google_preferred`: try Google if a healthy enabled integration exists; fallback to mock on controlled failure.
- `google_required`: try Google and leave meeting `failed` if Google cannot provision.
- `disabled`: no automatic meeting.

Supported config keys:

```json
{
  "calendar_id": "primary",
  "default_timezone": "America/Santiago",
  "send_updates": "none",
  "appointment_policy": "google_preferred",
  "fallback_provider": "mock"
}
```

## Transaction model

1. Persist appointment without calling external systems.
2. Create/update appointment meeting state as `pending`.
3. Commit appointment transaction.
4. Resolve provider.
5. Call provider outside appointment creation transaction.
6. Persist ready, fallback, failed, cancelled, or not-required state.
7. Update compatibility appointment meeting fields.
8. Notify using the resulting safe state.

If Google creates an event but local persistence fails, the idempotency key `appointment:<id>:meeting:create` allows manual retry/reconciliation without intentionally creating duplicates.

## Idempotency

- Creation key: `appointment:<appointment_id>:meeting:create`.
- Cancellation key: `appointment:<appointment_id>:meeting:cancel`.
- Existing ready/fallback/not-required/cancelled states return current local state.
- Failed creation can be retried manually by admin.

## Security

- Provider selection happens only in backend.
- Client payloads do not choose provider, calendar ID, attendees, or sendUpdates.
- Google events use neutral titles and minimal descriptions.
- Private notes, clinical/legal notes, OAuth tokens, raw metadata, and external event IDs are not exposed to client/professional.
- Admin sees provider, state, fallback, attempts, safe error code/message, and operations.

## Admin operations

- Retry creation.
- Retry cancellation.
- Reconcile by reading local/external state where possible.
- No automatic background retries.

## Debt for 12.4

- Integrated end-to-end validation with broader role workflows.
- More complete admin reservations UI for meeting operations.
- Operational runbook for production Google credentials.
- Future automatic retry/backoff strategy, if approved.
