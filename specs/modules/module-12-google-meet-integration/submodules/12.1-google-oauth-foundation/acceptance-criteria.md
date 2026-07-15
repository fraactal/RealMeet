# Acceptance criteria - Submodule 12.1

| Criterion | Status |
| --- | --- |
| Work starts from Module 11 close on a new Module 12 branch | Passed |
| Google OAuth settings added with safe defaults/placeholders | Passed |
| Backend starts without Google credentials | Passed |
| OAuth credential model and reversible migration added | Passed |
| Tokens are encrypted before persistence | Passed |
| State is signed, expiring, and one-time consumable | Passed |
| Authorization URL generation is admin-only and provider-checked | Passed |
| Callback stores safe credential data using fake client in tests | Passed |
| Refresh updates encrypted access token and expiry | Passed |
| Disconnect clears/inutilizes tokens and marks credential revoked | Passed |
| API never returns tokens, state, codes, or client secret | Passed |
| AuditLog records safe OAuth events | Passed |
| Backoffice allows only `google_meet` among future providers | Passed |
| Google Meet is not shown as meeting-operational in 12.1 | Passed |
| Mock integration and existing flows remain compatible | Passed |
| Tests, Alembic, build, health, and ready checks pass | Passed |
| No push, merge, deployment, real Google call, reservation change, or 12.2 work | Passed |
