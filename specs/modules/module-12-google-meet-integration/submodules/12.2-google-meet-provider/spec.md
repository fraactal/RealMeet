# Submodule 12.2 - Google Meet provider

## Objective

Implement a Google Meet provider capable of creating, reading, and cancelling meetings through Google Calendar events, using the OAuth foundation from 12.1. The provider remains isolated from automatic appointment creation until 12.3.

## Scope

- Add an internal meeting operation contract independent of Google.
- Add an injectable Google Calendar client with HTTP and fake-test paths.
- Create Calendar events with `conferenceDataVersion=1` and `hangoutsMeet`.
- Extract and validate safe Meet URLs.
- Persist reduced external meeting references.
- Use IntegrationExecution for idempotency and operation history.
- Refresh OAuth tokens before Calendar calls when needed.
- Implement Google Meet health check through a read-only calendar request.
- Add admin API endpoints for create/get/cancel meeting.
- Extend the integrations backoffice with an explicit test meeting form.
- Add focused automated tests using fakes and no real Google calls.

## Out of scope

- Automatic connection with appointments.
- Replacing `MockMeetingProvider`.
- Automatic invitations from appointment flows.
- Rescheduling, Google webhooks, background retries, APScheduler integration, multi-tenant OAuth, service accounts, WhatsApp, n8n, Microsoft, deployment, push, or merge.

## Architecture

- `GoogleCalendarClient`: HTTP serialization, Calendar event requests, response parsing, and Google error mapping.
- `GoogleMeetService`: RealMeet domain validation, OAuth credential handling, token refresh, idempotency, external meeting persistence, execution records, and audit.
- Admin API: protected orchestration only; no direct Google calls in routers.
- Backoffice: explicit manual test operation with confirmation and warnings.

## Contract

`MeetingCreateRequest` contains title, description, start/end datetimes, timezone, attendees, idempotency key, and sendUpdates. It does not contain tokens or OAuth details.

`MeetingResult` contains provider, external event id, calendar id, meeting URL, optional HTML link, optional conference id, status, start/end datetimes, and reduced metadata.

## Google event model

Create event uses:

- `conferenceDataVersion=1`
- `conferenceData.createRequest.requestId`
- `conferenceSolutionKey.type=hangoutsMeet`
- `sendUpdates` from integration/request policy

## Idempotency

Local idempotency uses `IntegrationExecution` by integration and idempotency key. A previous successful execution with persisted external event metadata returns the existing local meeting reference without calling Google again. Failed executions can be retried manually through the same idempotency key.

## Privacy

Do not store OAuth tokens, full Google responses, request/response headers, attendees by default, clinical details, private notes, or sensitive descriptions. Persist only reduced event references.

## Attendees and notifications

Admin test operation accepts optional attendee emails with limits and deduplication. `sendUpdates=none` is the default. `all` and `externalOnly` are explicit and should be treated as real invitation-sending modes.

## Timezone

Use IANA timezone names. Default: `America/Santiago`. Validate `start_at < end_at` and timezone correctness. Do not use fixed Chile offsets.

## Errors

Normalize OAuth not connected, refresh failure, invalid interval, invalid attendees, calendar not found, permissions, conference pending/failure, missing Meet URL, duplicate/idempotent operation, not found, already cancelled, timeout, and Google temporary/permanent errors.

## Tests

Automated tests use fake Calendar and fake OAuth only. No real Google network calls or credentials.

## Debt for 12.3

- Connect provider selection to appointment creation.
- Store appointment-to-external-meeting linkage.
- Define invitation policy for real appointments.
- Implement appointment cancellation/reconciliation fallback.
