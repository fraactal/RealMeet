from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.integrations.exceptions import IntegrationProviderExecutionError
from app.integrations.google_oauth import GoogleOAuthService
from app.integrations.google_workspace.docs_templates import (
    AppointmentGeneratedDocument,
    GenerateDocumentRequest,
    GoogleDocsDocumentType,
    GoogleDocsSharingPolicy,
    GoogleDocsTemplate,
    GoogleDocsTemplateCreate,
    GoogleDocsTemplateService,
    VARIABLE_REGISTRY,
    variable_catalog,
)
from app.main import app
from app.models.appointment import Appointment, AppointmentStatus, MeetingProvider
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import GoogleWorkspaceSettings, Integration, IntegrationCredential, IntegrationOAuthState
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService


class FakeDriveClient:
    def __init__(self, *, missing_source: bool = False, missing_folder: bool = False, fail_share: bool = False, missing_generated: bool = False) -> None:
        self.missing_source = missing_source
        self.missing_folder = missing_folder
        self.fail_share = fail_share
        self.missing_generated = missing_generated
        self.copied: list[dict] = []
        self.permissions: list[dict] = []

    def get_file_metadata(self, *, access_token: str, file_id: str) -> dict:
        del access_token
        if self.missing_source or (self.missing_generated and file_id.startswith("generated-")):
            raise IntegrationProviderExecutionError("Plantilla no encontrada", code="google_docs_template_not_found")
        return {"id": file_id, "name": "Plantilla", "mime_type": "application/vnd.google-apps.document", "trashed": False}

    def get_folder_metadata(self, *, access_token: str, folder_id: str) -> dict:
        del access_token
        if self.missing_folder:
            raise IntegrationProviderExecutionError("Carpeta no encontrada", code="google_drive_folder_not_found")
        return {"id": folder_id, "name": "Carpeta"}

    def copy_file(self, *, access_token: str, file_id: str, name: str, app_properties: dict[str, str] | None = None) -> dict:
        del access_token
        assert file_id == "source_doc_1234567890"
        copied = {"id": f"generated-{len(self.copied) + 1}", "name": name, "mime_type": "application/vnd.google-apps.document", "app_properties": app_properties or {}}
        self.copied.append(copied)
        return copied

    def move_file(self, *, access_token: str, file_id: str, folder_id: str) -> None:
        del access_token, file_id, folder_id

    def create_permission(self, *, access_token: str, file_id: str, email: str, role: str = "reader") -> dict:
        del access_token, file_id
        assert role == "reader"
        if self.fail_share:
            raise IntegrationProviderExecutionError("No compartido", code="google_drive_share_failed")
        permission = {"email": email, "role": role, "type": "user"}
        self.permissions.append(permission)
        return permission

    def delete_permission(self, *, access_token: str, file_id: str, permission_id: str) -> None:
        del access_token, file_id, permission_id


class FakeDocsClient:
    def __init__(self, text: str = "{{appointment_id}} {{client_name}} {{meeting_url}}") -> None:
        self.text = text
        self.replacements: list[dict[str, str]] = []

    def get_document(self, *, access_token: str, document_id: str) -> dict:
        del access_token
        return {"document_id": document_id, "title": "Plantilla", "text": self.text}

    def replace_all_text(self, *, access_token: str, document_id: str, replacements: dict[str, str]) -> None:
        del access_token
        assert document_id.startswith("generated-")
        self.replacements.append(replacements)


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 16.3%"))))
        template_ids = list(db.scalars(select(GoogleDocsTemplate.id).where(GoogleDocsTemplate.integration_id.in_(integration_ids)))) if integration_ids else []
        if template_ids:
            db.execute(delete(AppointmentGeneratedDocument).where(AppointmentGeneratedDocument.template_id.in_(template_ids)))
            db.execute(delete(GoogleDocsTemplate).where(GoogleDocsTemplate.id.in_(template_ids)))
        if integration_ids:
            db.execute(delete(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationOAuthState).where(IntegrationOAuthState.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        appointments = list(db.scalars(select(Appointment).where(Appointment.client_notes == "Test 16.3 clinical note")))
        if appointments:
            db.execute(delete(Appointment).where(Appointment.id.in_([item.id for item in appointments])))
        users = list(db.scalars(select(User).where(User.email.like("test-16-3-%@realmeet.local"))))
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
    user = User(
        email=f"test-16-3-{role.value}-{suffix}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name=role.value.title(),
        last_name=suffix,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _create_integration(db, admin: User) -> Integration:
    integration = IntegrationService(db).create_integration(
        IntegrationCreate(name="Test 16.3 google", integration_type=IntegrationType.meeting, provider=IntegrationProvider.google_meet, config={}, secret_reference=None),
        admin,
    )
    db.refresh(integration)
    return integration


def _authorize_workspace(db, integration: Integration, oauth_settings, *, docs=True, drive=True, scopes: list[str] | None = None) -> None:
    db.add(GoogleWorkspaceSettings(integration_id=integration.id, docs_enabled=docs, drive_enabled=drive, docs_authorized=docs, drive_authorized=drive))
    cipher = TokenCipher(oauth_settings.google_token_encryption_key)
    db.add(
        IntegrationCredential(
            integration_id=integration.id,
            credential_type="google_oauth",
            encrypted_access_token=cipher.encrypt("access-token-not-real"),
            encrypted_refresh_token=cipher.encrypt("refresh-token-not-real"),
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=scopes or ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.file"],
            external_account_email="docs-admin@example.test",
        )
    )
    db.commit()


def _service(db, oauth_settings, drive: FakeDriveClient | None = None, docs: FakeDocsClient | None = None) -> GoogleDocsTemplateService:
    return GoogleDocsTemplateService(db, oauth_service=GoogleOAuthService(db, app_settings=oauth_settings), drive_client=drive or FakeDriveClient(), docs_client=docs or FakeDocsClient())


def _template_payload(**overrides) -> GoogleDocsTemplateCreate:
    data = {
        "name": "Plantilla operacional",
        "description": "Resumen operativo",
        "document_type": GoogleDocsDocumentType.appointment_summary,
        "source_document_id": "source_doc_1234567890",
        "destination_folder_id": "folder_1234567890",
        "allowed_variables": ["appointment_id", "client_name", "meeting_url"],
        "sharing_policy": GoogleDocsSharingPolicy.private,
    }
    data.update(overrides)
    return GoogleDocsTemplateCreate(**data)


def _create_template(db, integration: Integration) -> GoogleDocsTemplate:
    item = GoogleDocsTemplate(integration_id=integration.id, **_template_payload().model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _create_appointment(db) -> Appointment:
    professional_user = _create_user(db, UserRole.professional, "prof")
    client_user = _create_user(db, UserRole.client, "client")
    professional = ProfessionalProfile(user_id=professional_user.id, consultation_mode=ConsultationMode.online, session_duration_minutes=45)
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    db.refresh(client)
    appointment = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        start_datetime=datetime(2026, 7, 20, 14, 0, tzinfo=UTC),
        end_datetime=datetime(2026, 7, 20, 14, 45, tzinfo=UTC),
        status=AppointmentStatus.confirmed,
        consultation_mode=ConsultationMode.online,
        meeting_provider=MeetingProvider.google_meet,
        meeting_url="https://meet.google.com/safe-doc",
        client_notes="Test 16.3 clinical note",
        professional_private_notes="diagnosis hidden",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def test_admin_can_create_template_and_roles_are_protected(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin")
    professional = _create_user(db_session, UserRole.professional, "professional")
    client = _create_user(db_session, UserRole.client, "client")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    path = f"/api/v1/admin/integrations/{integration.id}/google/workspace/docs/templates"

    response = api_client.post(path, headers=_headers(admin), json=_template_payload().model_dump(mode="json"))

    assert response.status_code == 200
    assert response.json()["source_document_id"] == "source_doc_1234567890"
    assert api_client.get(path, headers=_headers(professional)).status_code == 403
    assert api_client.get(path, headers=_headers(client)).status_code == 403


def test_workspace_requirements_and_variable_registry(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "requirements")
    integration = _create_integration(db_session, admin)
    service = _service(db_session, oauth_settings)

    _authorize_workspace(db_session, integration, oauth_settings, docs=False, drive=True)
    with pytest.raises(Exception, match="Docs esta deshabilitado"):
        service.create_template(integration.id, _template_payload())
    db_session.scalar(select(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id == integration.id)).docs_enabled = True
    db_session.scalar(select(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id == integration.id)).drive_enabled = False
    db_session.commit()
    with pytest.raises(Exception, match="Drive esta deshabilitado"):
        service.create_template(integration.id, _template_payload())
    credential = db_session.scalar(select(IntegrationCredential).where(IntegrationCredential.integration_id == integration.id))
    db_session.scalar(select(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id == integration.id)).drive_enabled = True
    credential.scopes = ["https://www.googleapis.com/auth/drive.file"]
    db_session.commit()
    with pytest.raises(Exception, match="Docs requiere autorizacion"):
        service.create_template(integration.id, _template_payload())
    credential.scopes = ["https://www.googleapis.com/auth/documents"]
    db_session.commit()
    with pytest.raises(Exception, match="Drive requiere autorizacion"):
        service.create_template(integration.id, _template_payload())

    catalog = variable_catalog()
    assert "clinical_notes" not in VARIABLE_REGISTRY
    assert all(not item.sensitive for item in catalog)
    with pytest.raises(Exception, match="Variable no permitida"):
        _template_payload(allowed_variables=["diagnosis"])


def test_validate_template_metadata_folder_and_variables(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "validate")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _create_template(db_session, integration)

    result = _service(db_session, oauth_settings).validate_template(integration.id, template.id)

    assert result.valid is True
    assert "Plantilla" in result.document["name"]
    assert "{{appointment_id}}" in result.placeholders
    assert "Plantilla operacional" not in str(result)
    with pytest.raises(Exception, match="Plantilla"):
        _service(db_session, oauth_settings, FakeDriveClient(missing_source=True)).validate_template(integration.id, template.id)
    with pytest.raises(Exception, match="Carpeta"):
        _service(db_session, oauth_settings, FakeDriveClient(missing_folder=True)).validate_template(integration.id, template.id)
    with pytest.raises(Exception, match="variables no permitidas"):
        _service(db_session, oauth_settings, docs=FakeDocsClient("{{clinical_notes}}")).validate_template(integration.id, template.id)


def test_generate_private_share_policies_idempotency_retry_and_reconcile(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "generate")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _create_template(db_session, integration)
    appointment = _create_appointment(db_session)
    drive = FakeDriveClient()
    docs = FakeDocsClient()
    service = _service(db_session, oauth_settings, drive, docs)

    private_doc = service.generate(appointment.id, GenerateDocumentRequest(template_id=template.id, sharing_policy=GoogleDocsSharingPolicy.private, generation_request_id="req-private"), admin)
    same = service.generate(appointment.id, GenerateDocumentRequest(template_id=template.id, sharing_policy=GoogleDocsSharingPolicy.private, generation_request_id="req-private"), admin)
    professional = service.generate(appointment.id, GenerateDocumentRequest(template_id=template.id, sharing_policy=GoogleDocsSharingPolicy.professional_only, generation_request_id="req-prof"), admin)
    both = service.generate(appointment.id, GenerateDocumentRequest(template_id=template.id, sharing_policy=GoogleDocsSharingPolicy.professional_and_client, generation_request_id="req-both"), admin)

    assert private_doc.id == same.id
    assert len(drive.copied) == 3
    assert private_doc.sharing_status == "private"
    assert professional.sharing_status == "shared"
    assert both.sharing_status == "shared"
    assert all(permission["role"] == "reader" and permission["type"] == "user" for permission in drive.permissions)
    assert len(drive.permissions) == 3
    replacements = str(docs.replacements)
    assert "diagnosis hidden" not in replacements
    assert "clinical note" not in replacements
    assert "access-token" not in str(private_doc.__dict__)

    failing_drive = FakeDriveClient(fail_share=True)
    partial = _service(db_session, oauth_settings, failing_drive, FakeDocsClient()).generate(
        appointment.id,
        GenerateDocumentRequest(template_id=template.id, sharing_policy=GoogleDocsSharingPolicy.professional_only, generation_request_id="req-fail-share"),
        admin,
    )
    assert partial.status == "partially_generated"
    assert partial.external_file_id is not None
    copied_before = len(failing_drive.copied)
    retried = _service(db_session, oauth_settings, failing_drive, FakeDocsClient()).retry(appointment.id, partial.id)
    assert retried.id == partial.id
    assert len(failing_drive.copied) == copied_before

    reconciled = service.reconcile(appointment.id, private_doc.id)
    assert reconciled.result == "external_document_found"
    missing = _service(db_session, oauth_settings, FakeDriveClient(missing_generated=True)).reconcile(appointment.id, private_doc.id)
    assert missing.result == "external_document_missing"


def test_api_tokens_are_not_returned_and_reconcile_endpoint(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "api")
    integration = _create_integration(db_session, admin)
    _authorize_workspace(db_session, integration, oauth_settings)
    template = _create_template(db_session, integration)
    appointment = _create_appointment(db_session)

    response = api_client.get(f"/api/v1/admin/appointments/{appointment.id}/documents", headers=_headers(admin))

    assert response.status_code == 200
    assert "access-token" not in response.text
    assert "refresh-token" not in response.text
    assert template.enabled is True
