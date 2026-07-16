from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.automation.enums import WebhookDeliveryStatus
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.integrations.exceptions import IntegrationProviderExecutionError
from app.integrations.google_oauth import GoogleOAuthService
from app.integrations.google_workspace.docs_templates import GoogleDocsDocumentType, GoogleDocsSharingPolicy, GoogleDocsTemplate, GoogleDocsTemplateCreate, GoogleDocsTemplateService
from app.integrations.google_workspace.document_automation import (
    DocumentAutomationEmailRecipientPolicy,
    DocumentAutomationEmailStatus,
    DocumentAutomationEventType,
    DocumentAutomationExecution,
    DocumentAutomationExecutionStatus,
    DocumentAutomationN8nStatus,
    DocumentAutomationService,
    GoogleDocsAutomationRule,
    GoogleDocsAutomationRuleCreate,
)
from app.main import app
from app.models.appointment import Appointment, AppointmentStatus, MeetingProvider
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import GoogleWorkspaceSettings, Integration, IntegrationCredential, IntegrationOAuthState
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.models.webhook import WebhookDelivery, WebhookSubscription
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService


class FakeDriveClient:
    def __init__(self, *, fail_share: bool = False, missing_generated: bool = False) -> None:
        self.fail_share = fail_share
        self.missing_generated = missing_generated
        self.copied: list[dict] = []
        self.permissions: list[dict] = []

    def get_file_metadata(self, *, access_token: str, file_id: str) -> dict:
        del access_token
        if self.missing_generated and file_id.startswith("generated-"):
            raise IntegrationProviderExecutionError("No encontrado", code="google_generated_document_not_found")
        return {"id": file_id, "name": "Plantilla", "mime_type": "application/vnd.google-apps.document", "trashed": False}

    def get_folder_metadata(self, *, access_token: str, folder_id: str) -> dict:
        del access_token
        return {"id": folder_id, "name": "Carpeta"}

    def copy_file(self, *, access_token: str, file_id: str, name: str, app_properties: dict[str, str] | None = None) -> dict:
        del access_token, file_id
        copied = {"id": f"generated-{len(self.copied) + 1}", "name": name, "app_properties": app_properties or {}}
        self.copied.append(copied)
        return copied

    def move_file(self, *, access_token: str, file_id: str, folder_id: str) -> None:
        del access_token, file_id, folder_id

    def create_permission(self, *, access_token: str, file_id: str, email: str, role: str = "reader") -> dict:
        del access_token, file_id
        if self.fail_share:
            raise IntegrationProviderExecutionError("No compartido", code="google_drive_share_failed")
        item = {"email": email, "role": role}
        self.permissions.append(item)
        return item


class FakeDocsClient:
    def __init__(self) -> None:
        self.replacements: list[dict[str, str]] = []

    def get_document(self, *, access_token: str, document_id: str) -> dict:
        del access_token
        return {"document_id": document_id, "title": "Plantilla", "text": "{{appointment_id}} {{client_name}} {{meeting_url}}"}

    def replace_all_text(self, *, access_token: str, document_id: str, replacements: dict[str, str]) -> None:
        del access_token, document_id
        self.replacements.append(replacements)


class FakeMailer:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, str, str]] = []

    def send(self, subject: str, recipient: str, body: str) -> bool:
        self.sent.append((subject, recipient, body))
        return not self.fail


class FakeWebhookService:
    def __init__(self, *, status: WebhookDeliveryStatus | None = WebhookDeliveryStatus.succeeded) -> None:
        self.status = status
        self.events: list[dict] = []

    def publish(self, event):
        self.events.append(event.as_payload())
        if self.status is None:
            return []
        return [SimpleNamespace(status=self.status)]


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 16.4%"))))
        rule_ids = list(db.scalars(select(GoogleDocsAutomationRule.id).where(GoogleDocsAutomationRule.integration_id.in_(integration_ids)))) if integration_ids else []
        template_ids = list(db.scalars(select(GoogleDocsTemplate.id).where(GoogleDocsTemplate.integration_id.in_(integration_ids)))) if integration_ids else []
        if rule_ids:
            db.execute(delete(DocumentAutomationExecution).where(DocumentAutomationExecution.rule_id.in_(rule_ids)))
            db.execute(delete(GoogleDocsAutomationRule).where(GoogleDocsAutomationRule.id.in_(rule_ids)))
        if template_ids:
            from app.integrations.google_workspace.docs_templates import AppointmentGeneratedDocument

            db.execute(delete(AppointmentGeneratedDocument).where(AppointmentGeneratedDocument.template_id.in_(template_ids)))
            db.execute(delete(GoogleDocsTemplate).where(GoogleDocsTemplate.id.in_(template_ids)))
        if integration_ids:
            db.execute(delete(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationOAuthState).where(IntegrationOAuthState.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
            db.execute(delete(WebhookDelivery).where(WebhookDelivery.subscription_id.in_(select(WebhookSubscription.id).where(WebhookSubscription.integration_id.in_(integration_ids)))))
            db.execute(delete(WebhookSubscription).where(WebhookSubscription.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        appointments = list(db.scalars(select(Appointment).where(Appointment.client_notes == "Test 16.4 clinical note")))
        if appointments:
            db.execute(delete(Appointment).where(Appointment.id.in_([item.id for item in appointments])))
        users = list(db.scalars(select(User).where(User.email.like("test-16-4-%@realmeet.local"))))
        user_ids = [item.id for item in users]
        if user_ids:
            db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.user_id.in_(user_ids)))
            db.execute(delete(ClientProfile).where(ClientProfile.user_id.in_(user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def oauth_settings():
    return settings.model_copy(update={"google_token_encryption_key": Fernet.generate_key().decode()})


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(email=f"test-16-4-{role.value}-{suffix}@realmeet.local", password_hash=hash_password("Secret123!"), first_name=role.value.title(), last_name=suffix, role=role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _create_integration(db, admin: User) -> Integration:
    integration = IntegrationService(db).create_integration(IntegrationCreate(name="Test 16.4 google", integration_type=IntegrationType.meeting, provider=IntegrationProvider.google_meet, config={}, secret_reference=None), admin)
    db.refresh(integration)
    return integration


def _authorize_workspace(db, integration: Integration, oauth_settings) -> None:
    db.add(GoogleWorkspaceSettings(integration_id=integration.id, docs_enabled=True, drive_enabled=True, docs_authorized=True, drive_authorized=True))
    cipher = TokenCipher(oauth_settings.google_token_encryption_key)
    db.add(IntegrationCredential(integration_id=integration.id, credential_type="google_oauth", encrypted_access_token=cipher.encrypt("access-token-not-real"), encrypted_refresh_token=cipher.encrypt("refresh-token-not-real"), token_type="Bearer", expires_at=datetime.now(UTC) + timedelta(hours=1), scopes=["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.file"], external_account_email="docs-admin@example.test"))
    db.commit()


def _docs_service(db, oauth_settings, drive: FakeDriveClient | None = None, docs: FakeDocsClient | None = None) -> GoogleDocsTemplateService:
    return GoogleDocsTemplateService(db, oauth_service=GoogleOAuthService(db, app_settings=oauth_settings), drive_client=drive or FakeDriveClient(), docs_client=docs or FakeDocsClient())


def _template(db, integration: Integration, *, enabled: bool = True, policy: GoogleDocsSharingPolicy = GoogleDocsSharingPolicy.professional_and_client) -> GoogleDocsTemplate:
    payload = GoogleDocsTemplateCreate(name="Test 16.4 plantilla", document_type=GoogleDocsDocumentType.appointment_confirmation, source_document_id="source_doc_1234567890", destination_folder_id=None, enabled=enabled, allowed_variables=["appointment_id", "client_name", "meeting_url"], sharing_policy=policy)
    item = GoogleDocsTemplate(integration_id=integration.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _appointment(db) -> Appointment:
    professional_user = _create_user(db, UserRole.professional, "prof")
    client_user = _create_user(db, UserRole.client, "client")
    professional = ProfessionalProfile(user_id=professional_user.id, consultation_mode=ConsultationMode.online, session_duration_minutes=45)
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    db.refresh(client)
    appointment = Appointment(professional_id=professional.id, client_id=client.id, start_datetime=datetime(2026, 7, 20, 14, 0, tzinfo=UTC), end_datetime=datetime(2026, 7, 20, 14, 45, tzinfo=UTC), status=AppointmentStatus.confirmed, consultation_mode=ConsultationMode.online, meeting_provider=MeetingProvider.google_meet, meeting_url="https://meet.google.com/safe-doc", client_notes="Test 16.4 clinical note", professional_private_notes="diagnosis hidden")
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def _rule(db, integration: Integration, template: GoogleDocsTemplate, **overrides) -> GoogleDocsAutomationRule:
    data = {
        "template_id": template.id,
        "name": "Regla 16.4",
        "description": "Genera documento operacional",
        "event_type": DocumentAutomationEventType.appointment_created,
        "enabled": True,
        "sharing_policy": template.sharing_policy,
        "email_delivery_enabled": False,
        "email_recipient_policy": DocumentAutomationEmailRecipientPolicy.none,
        "n8n_event_enabled": False,
    }
    data.update(overrides)
    return DocumentAutomationService(db).create_rule(integration.id, GoogleDocsAutomationRuleCreate(**data))


def _automation(db, oauth_settings, *, drive=None, mailer=None, webhook=None) -> DocumentAutomationService:
    return DocumentAutomationService(db, docs_service=_docs_service(db, oauth_settings, drive=drive), mailer=mailer or FakeMailer(), webhook_service=webhook or FakeWebhookService(status=None))


def test_admin_can_create_rule_and_roles_are_protected(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin")
    professional = _create_user(db_session, UserRole.professional, "professional")
    client = _create_user(db_session, UserRole.client, "client")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    path = f"/api/v1/admin/integrations/{integration.id}/google/workspace/docs/automation-rules"
    payload = GoogleDocsAutomationRuleCreate(template_id=template.id, name="Regla API", event_type=DocumentAutomationEventType.appointment_created).model_dump(mode="json")

    response = api_client.post(path, headers=_headers(admin), json=payload)

    assert response.status_code == 200
    assert response.json()["event_type"] == "appointment.created"
    assert api_client.get(path, headers=_headers(professional)).status_code == 403
    assert api_client.get(path, headers=_headers(client)).status_code == 403


def test_disabled_template_and_invalid_event_are_rejected(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-invalid")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration, enabled=False)
    path = f"/api/v1/admin/integrations/{integration.id}/google/workspace/docs/automation-rules"

    payload = GoogleDocsAutomationRuleCreate(template_id=template.id, name="Mala", event_type=DocumentAutomationEventType.appointment_created).model_dump(mode="json")
    response = api_client.post(path, headers=_headers(admin), json=payload)
    payload["event_type"] = "clinical.note.created"
    invalid = api_client.post(path, headers=_headers(admin), json=payload)

    assert response.status_code == 422
    assert invalid.status_code == 422


def test_disabled_rule_and_unconfigured_event_do_not_generate(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "disabled")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template, enabled=False)

    executions = _automation(db_session, oauth_settings).handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, actor=admin)
    no_event = _automation(db_session, oauth_settings).handle_appointment_event(DocumentAutomationEventType.appointment_cancelled, appointment, actor=admin)

    assert executions == []
    assert no_event == []


def test_appointment_created_generates_document_and_is_idempotent(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "generate")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template)
    drive = FakeDriveClient()
    service = _automation(db_session, oauth_settings, drive=drive)

    first = service.handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-1", actor=admin)[0]
    second = service.handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-1", actor=admin)[0]

    assert first.id == second.id
    assert first.generated_document_id is not None
    assert len(drive.copied) == 1
    assert "diagnosis" not in (first.error_message or "")


def test_email_recipients_follow_policy_after_sharing(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "email")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    mailer = FakeMailer()
    _rule(db_session, integration, template, email_delivery_enabled=True, email_recipient_policy=DocumentAutomationEmailRecipientPolicy.professional_and_client)

    execution = _automation(db_session, oauth_settings, mailer=mailer).handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-email", actor=admin)[0]

    assert execution.email_status == DocumentAutomationEmailStatus.sent
    assert {item[1] for item in mailer.sent} == {appointment.professional.user.email, appointment.client.user.email}
    assert all("diagnosis" not in item[2] and "token" not in item[2] for item in mailer.sent)


def test_email_skips_when_document_is_private_or_sharing_fails(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "email-skip")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration, policy=GoogleDocsSharingPolicy.private)
    appointment = _appointment(db_session)
    mailer = FakeMailer()
    _rule(db_session, integration, template, email_delivery_enabled=True, email_recipient_policy=DocumentAutomationEmailRecipientPolicy.professional)

    execution = _automation(db_session, oauth_settings, mailer=mailer).handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-private", actor=admin)[0]

    assert execution.email_status == DocumentAutomationEmailStatus.skipped
    assert execution.status == DocumentAutomationExecutionStatus.partially_succeeded
    assert mailer.sent == []


def test_n8n_document_generated_event_and_skipped_without_workflow(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "n8n")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template, n8n_event_enabled=True)
    webhook = FakeWebhookService(status=WebhookDeliveryStatus.succeeded)

    execution = _automation(db_session, oauth_settings, webhook=webhook).handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-n8n", actor=admin)[0]

    payload = webhook.events[0]
    assert execution.n8n_status == DocumentAutomationN8nStatus.delivered
    assert payload["event_type"] == "document.generated"
    assert "diagnosis" not in str(payload)
    assert "access-token" not in str(payload)


def test_partial_status_for_email_and_n8n_failures(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "partial")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template, email_delivery_enabled=True, email_recipient_policy=DocumentAutomationEmailRecipientPolicy.professional, sharing_policy=GoogleDocsSharingPolicy.professional_only, n8n_event_enabled=True)

    execution = _automation(db_session, oauth_settings, mailer=FakeMailer(fail=True), webhook=FakeWebhookService(status=WebhookDeliveryStatus.failed)).handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-partial", actor=admin)[0]

    assert execution.status == DocumentAutomationExecutionStatus.partially_succeeded
    assert execution.email_status == DocumentAutomationEmailStatus.failed
    assert execution.n8n_status == DocumentAutomationN8nStatus.failed


def test_generation_failure_is_sanitized_and_does_not_delete_appointment(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "failure")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template)

    execution = _automation(db_session, oauth_settings, drive=FakeDriveClient(fail_share=True)).handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-fail", actor=admin)[0]

    assert db_session.get(Appointment, appointment.id) is not None
    assert execution.status == DocumentAutomationExecutionStatus.partially_succeeded
    assert "Traceback" not in (execution.error_message or "")


def test_retry_does_not_duplicate_document_or_completed_steps(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "retry")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template, email_delivery_enabled=True, email_recipient_policy=DocumentAutomationEmailRecipientPolicy.professional, sharing_policy=GoogleDocsSharingPolicy.professional_only, n8n_event_enabled=True)
    drive = FakeDriveClient()
    mailer = FakeMailer(fail=True)
    webhook = FakeWebhookService(status=WebhookDeliveryStatus.succeeded)
    service = _automation(db_session, oauth_settings, drive=drive, mailer=mailer, webhook=webhook)
    execution = service.handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-retry", actor=admin)[0]
    mailer.fail = False

    retried = service.retry_execution(integration.id, execution.id, admin)

    assert retried.id == execution.id
    assert len(drive.copied) == 1
    assert len(webhook.events) == 1
    assert retried.email_status == DocumentAutomationEmailStatus.sent


def test_reconcile_detects_missing_and_partial_state(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "reconcile")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _template(db_session, integration)
    appointment = _appointment(db_session)
    _rule(db_session, integration, template)
    service = _automation(db_session, oauth_settings)
    execution = service.handle_appointment_event(DocumentAutomationEventType.appointment_created, appointment, event_id="evt-reconcile", actor=admin)[0]

    result = service.reconcile_execution(integration.id, execution.id)
    execution.generated_document_id = None
    db_session.commit()
    missing = service.reconcile_execution(integration.id, execution.id)

    assert result.result in {"in_sync", "partial", "email_pending", "n8n_pending"}
    assert missing.result == "document_missing"
