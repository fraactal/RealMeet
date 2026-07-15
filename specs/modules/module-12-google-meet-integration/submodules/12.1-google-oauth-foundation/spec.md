# Submodule 12.1 - Google OAuth foundation

## Objective

Prepare the secure backend and admin backoffice foundation required to authorize a Google account for a `google_meet` integration. This submodule does not create Google Calendar events or Google Meet links.

## Scope

- Create Module 12 branch and documentation.
- Add Google OAuth settings with safe empty defaults.
- Add persistent OAuth credential storage linked to `Integration`.
- Encrypt OAuth tokens before persistence.
- Add signed and expiring OAuth state with one-time consumption.
- Add an abstract Google OAuth client plus a prepared HTTP implementation and fake client support for tests.
- Add admin API endpoints for authorization URL generation, callback handling, OAuth status, refresh, and disconnect.
- Register `google_meet` as a prepared integration provider, not an operational meeting creator.
- Extend the admin integrations backoffice to create Google Meet integrations and show OAuth connection actions.
- Add focused tests without real Google calls.

## Out of scope

- Real meeting creation.
- Google Calendar event creation.
- Reservation integration.
- Invite emails.
- Google webhooks, watch channels, service accounts, domain-wide delegation, professional-level OAuth, workers, scheduled refresh, deployment, push, merge, WhatsApp, Twilio, n8n, or Microsoft providers.

## Actors

- Admin: creates a `google_meet` integration, starts OAuth, handles callback, views status, refreshes token manually in tests, and disconnects.
- Client/professional: no OAuth access.
- Google authorization server: external system prepared for future use, not called in automated tests.

## OAuth flow

1. Admin creates a `google_meet` integration.
2. Admin requests an authorization URL.
3. Backend verifies provider and Google OAuth settings.
4. Backend creates a signed state with integration id, admin id, nonce, and expiry.
5. Admin visits Google authorization URL.
6. Callback receives `code` and `state`.
7. Backend validates and consumes state.
8. Backend exchanges code through an injectable OAuth client.
9. Tokens are encrypted and stored in `integration_credentials`.
10. Integration status becomes configured.
11. Backoffice shows connected status without tokens.

## Threat model

- Prevent callback tampering through signed expiring state.
- Prevent replay through one-time state nonce consumption.
- Prevent provider confusion by requiring `google_meet`.
- Prevent token disclosure by encrypting tokens and never returning them through API.
- Prevent logging secrets by keeping audit metadata minimal.
- Prevent user-supplied redirect URI by using settings only.

## Credentials and tokens

- Application OAuth credentials live only in environment variables.
- Account authorization tokens live in `integration_credentials` encrypted columns.
- `Integration.config` stores only non-secret data.
- `Integration.secret_reference` may point to an operational configuration reference but never stores token values.

## Scopes

Centralized scope:

- `https://www.googleapis.com/auth/calendar.events`

Reason: needed in 12.2 to create Google Calendar events with conference data for Google Meet. Gmail, Drive, contacts, profile, and broad Calendar scopes are intentionally excluded.

## States

Derived OAuth status:

- `not_connected`
- `pending`
- `connected`
- `expired`
- `revoked`
- `error`

The persisted credential stores revocation and expiry data; the public API returns only a safe summary.

## Revocation

Disconnect performs local revocation by marking the credential revoked and clearing encrypted token fields. Remote revocation is prepared through the OAuth client interface but failures do not keep the integration connected.

## Audit

Events:

- authorization started;
- authorization completed;
- authorization failed;
- token refreshed;
- integration disconnected.

Audit metadata excludes URLs with state, authorization code, tokens, client secret, and full OAuth responses.

## Tests

Tests use fake OAuth clients and fake tokens only. No test calls Google.

## Debt for 12.2

- Create Google Calendar events with conference data.
- Resolve and refresh tokens during meeting creation.
- Map calendar event id and Meet link to appointments.
- Handle provider-specific operational health checks.
- Add staging validation with real OAuth credentials outside automated tests.
