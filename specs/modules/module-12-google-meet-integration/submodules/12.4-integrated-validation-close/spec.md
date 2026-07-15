# Submodule 12.4 - Integrated validation and close

## Objective

Validate Module 12 end to end and close the Google Meet integration work without adding new product capabilities.

## Scope

- Verify migrations, persistence, OAuth, encryption, Calendar client, Google Meet provider, appointments integration, fallback, idempotency, cancellation, reconciliation, role visibility, email behavior, scheduler impact, backoffice, frontend states, security, and documentation.
- Correct only real defects found during validation.
- Produce the final Module 12 report.

## Out of scope

- Push, merge, tags, deployment, Module 13, new providers, automatic retries, Google webhooks, bidirectional sync, rescheduling, professional OAuth, production readiness claims, or real Google calls in automated tests.

## Flow matrix

| Flow | Expected result |
| --- | --- |
| Google OAuth authorization | Admin only, state protected, tokens encrypted |
| Google Meet manual create | Admin explicit action, idempotent, no attendees by default |
| Appointment confirm with `mock_only` | Mock meeting ready |
| Appointment confirm with `google_preferred` and Google healthy | Google meeting ready |
| Appointment confirm with `google_preferred` and Google failure | Mock fallback, admin sees safe reason |
| Appointment confirm with `google_required` and Google failure | Appointment remains, meeting failed |
| Appointment confirm with `disabled` | Meeting not required |
| Appointment cancel with Google | Best-effort external cancellation |
| Appointment cancel with failure | Appointment remains cancelled, admin can retry |
| Reconcile | Manual local/external status refresh, no auto recreate |

## Policy matrix

| Policy | Google used | Mock used | Failure behavior |
| --- | --- | --- | --- |
| `mock_only` | No | Yes | Mock errors are local failures |
| `google_preferred` | Yes when healthy | Yes on controlled Google failure | Fallback state |
| `google_required` | Yes | No | Meeting failed, reservation intact |
| `disabled` | No | No | `not_required` |

## Role matrix

| Role | Visibility | Operations |
| --- | --- | --- |
| Client | Own meeting state, neutral message, link when ready | No admin operations |
| Professional | Authorized reservation meeting state/link | No integration operations |
| Admin | Provider, policy, fallback, error summary, retry/reconcile | OAuth, policy, manual test, retry, reconcile |

## Risks

- Real Google behavior remains unverified without a controlled Google Cloud account.
- No background reconciliation exists.
- Policy is global per selected Google Meet integration, not per professional.
- Email timing depends on meeting provisioning finishing before confirmation notification.

## Decision target

Module 12 can be considered locally complete if tests/build/runtime checks pass, no secrets are introduced, no out-of-scope work appears in the diff, and limitations are documented.
