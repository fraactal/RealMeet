# Implementation status - Submodule 12.3

Status: implemented.

## Initial findings

- `MockMeetingProvider` is intact.
- `AppointmentService` currently creates a meeting before appointment persistence.
- Reservation responses already contain `meeting_provider`, `meeting_url`, and `meeting`.
- Notifications read the appointment object and include the URL only on confirmation.
- Scheduler does not provision meetings.

## Implemented

- Added `AppointmentMeeting` model and migration `20260715_0007`.
- Extended `ExternalMeeting` with nullable `appointment_id`.
- Added `MeetingProvisioningService` for policy resolution, provider selection, fallback, idempotent local state, cancellation, retry, and reconciliation.
- Updated `AppointmentService` so appointment creation no longer calls a meeting provider before persistence. Meeting provisioning runs after confirmation.
- Cancellation remains committed even when external meeting cancellation fails.
- Added admin endpoints:
  - `POST /api/v1/admin/appointments/{appointment_id}/meeting/retry-create`
  - `POST /api/v1/admin/appointments/{appointment_id}/meeting/retry-cancel`
  - `POST /api/v1/admin/appointments/{appointment_id}/meeting/reconcile`
- Extended appointment schemas with safe meeting state, fallback flag, neutral message, and admin-only error fields.
- Updated client/professional/admin cards and admin reservations backoffice actions.
- Added integration config controls for `appointment_policy`, calendar ID, timezone, sendUpdates, fallback provider, and optional attendee inclusion.
- Added fake-based backend tests for policy resolution, Google success, fallback, required failure, disabled, idempotency, cancellation, and safe client contract.

## Transaction behavior

- Appointment row is committed before any external provider call.
- Meeting link is moved through `pending`, `provisioning`, `ready`, `fallback_ready`, `failed`, `cancelled`, or `not_required`.
- Google idempotency uses `appointment:<id>:meeting:create`.
- Cancellation idempotency uses `appointment:<id>:meeting:cancel`.
- No background retry or scheduler job was added.

## Limitations

- Reconciliation is manual and basic.
- No automatic retry/backoff.
- No bidirectional Google sync.
- No rescheduling support.
- Policy is global through the selected Google Meet integration, not per professional.
