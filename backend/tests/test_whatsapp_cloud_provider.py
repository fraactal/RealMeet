from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.models.audit_log import AuditLog
from app.models.integration import Integration, IntegrationExecution
from app.models.user import User, UserRole
from app.models.whatsapp import WhatsAppConsent, WhatsAppMessage, WhatsAppTemplate, WhatsAppWebhookEvent
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService
from app.whatsapp.cloud_client import FakeWhatsAppCloudClient, WhatsAppRemoteTemplate
from app.whatsapp.enums import WhatsAppConsentPurpose, WhatsAppConsentSource, WhatsAppConsentStatus, WhatsAppMessageStatus, WhatsAppTemplateCategory, WhatsAppTemplatePurpose, WhatsAppTemplateStatus, WhatsAppWebhookEventType
from app.whatsapp.exceptions import WhatsAppValidationError
from app.whatsapp.messaging import WhatsAppMessagingService
from app.whatsapp.phone import normalize_phone, phone_hmac
from app.whatsapp.schemas import WhatsAppMessageSendRequest
from app.main import app


@pytest.fixture(autouse=True)
def whatsapp_env(monkeypatch) -> None:
    monkeypatch.setattr(settings, "whatsapp_phone_hmac_key", "test-whatsapp-hmac-key")
    monkeypatch.setattr(settings, "whatsapp_default_country_code", "CL")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "fake-token")


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 13.2%"))))
        if integration_ids:
            db.execute(delete(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.integration_id.in_(integration_ids)))
            db.execute(delete(WhatsAppMessage).where(WhatsAppMessage.integration_id.in_(integration_ids)))
            db.execute(delete(WhatsAppTemplate).where(WhatsAppTemplate.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationExecution).where(IntegrationExecution.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        user_ids = list(db.scalars(select(User.id).where(User.email.like("test-13-2-%@realmeet.local"))))
        if user_ids:
            db.execute(delete(WhatsAppConsent).where(WhatsAppConsent.user_id.in_(user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.action.like("whatsapp_%")))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-13-2-{suffix}-{uuid4().hex[:8]}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name=suffix.title(),
        role=role,
        phone="+56912345678",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _config() -> dict:
    return {
        "waba_id": "123456789",
        "phone_number_id": "987654321",
        "display_phone_number_masked": "+56 9 **** 5678",
        "graph_api_version": "v20.0",
        "default_language": "es_CL",
        "country_code": "CL",
        "secret_references": {"access_token": "WHATSAPP_ACCESS_TOKEN", "phone_hmac_key": "WHATSAPP_PHONE_HMAC_KEY"},
    }


def _integration(db, admin: User | None = None, *, enabled: bool = True) -> Integration:
    admin_user = admin or _create_user(db, UserRole.admin, "admin")
    item = IntegrationService(db).create_integration(
        IntegrationCreate(name=f"Test 13.2 WhatsApp {uuid4().hex[:6]}", integration_type=IntegrationType.messaging, provider=IntegrationProvider.whatsapp_cloud, config=_config()),
        admin_user,
    )
    if enabled:
        IntegrationService(db).enable_integration(item.id, admin_user)
    return item


def _template(db, integration: Integration, *, status=WhatsAppTemplateStatus.approved, category=WhatsAppTemplateCategory.utility, name: str | None = None) -> WhatsAppTemplate:
    template = WhatsAppTemplate(
        integration_id=integration.id,
        name=name or f"appointment_confirmation_{uuid4().hex[:8]}",
        language="es_CL",
        category=category,
        status=status,
        purpose=WhatsAppTemplatePurpose.appointment_confirmation,
        components_schema={"variables": [{"key": "client_name", "required": True, "sensitive": False}]},
        external_template_id="tmpl_fake_1",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def _consent(db, user: User, *, status=WhatsAppConsentStatus.granted, purpose=WhatsAppConsentPurpose.appointment_transactional) -> WhatsAppConsent:
    phone = normalize_phone("+56912345678")
    consent = WhatsAppConsent(
        user_id=user.id,
        phone_e164=phone.e164,
        phone_hash=phone_hmac(phone.e164),
        phone_masked=phone.masked,
        status=status,
        purpose=purpose,
        source=WhatsAppConsentSource.admin_correction,
        consent_text_version="wa-test",
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def _send_payload(consent: WhatsAppConsent, template: WhatsAppTemplate, *, key: str = "manual:test:13.2") -> WhatsAppMessageSendRequest:
    return WhatsAppMessageSendRequest(
        consent_id=consent.id,
        template_id=template.id,
        purpose=WhatsAppTemplatePurpose.appointment_confirmation,
        language="es_CL",
        variables={"client_name": "Cliente Demo"},
        idempotency_key=key,
        explicit_confirmation=True,
    )


def test_fake_client_builds_template_payload_without_network() -> None:
    client = FakeWhatsAppCloudClient()
    result = client.send_template_message(graph_api_version="v20.0", phone_number_id="987654321", access_token="secret", to_e164="+56912345678", template_name="demo", language="es_CL", body_variables=["Cliente"])
    assert result.external_message_id.startswith("wamid.fake.")
    assert client.sent_payloads[0]["messaging_product"] == "whatsapp"
    assert client.sent_payloads[0]["type"] == "template"
    assert client.sent_payloads[0]["url"] == "https://graph.facebook.com/v20.0/987654321/messages"
    assert "secret" not in str(client.sent_payloads[0])


def test_send_requires_enabled_integration_token_consent_and_approved_template(db_session, monkeypatch) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-send")
    client_user = _create_user(db_session, UserRole.client, "client-send")
    integration = _integration(db_session, admin)
    template = _template(db_session, integration)
    consent = _consent(db_session, client_user)
    result = WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient()).send_template(integration, _send_payload(consent, template), admin)
    assert result.success is True
    assert result.data.status == WhatsAppMessageStatus.accepted
    stored = db_session.get(WhatsAppMessage, result.data.id)
    assert stored is not None
    assert stored.recipient_masked != consent.phone_e164
    assert stored.external_message_id == "wamid.fake.1"

    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN")
    with pytest.raises(WhatsAppValidationError, match="Token WhatsApp"):
        WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient()).send_template(integration, _send_payload(consent, template, key="manual:test:no-token"), admin)


def test_send_blocks_revoked_consent_draft_marketing_and_bad_variables(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-block")
    client_user = _create_user(db_session, UserRole.client, "client-block")
    integration = _integration(db_session, admin)
    draft = _template(db_session, integration, status=WhatsAppTemplateStatus.draft, name="appointment_confirmation_draft")
    approved = _template(db_session, integration, name="appointment_confirmation_approved")
    revoked = _consent(db_session, client_user, status=WhatsAppConsentStatus.revoked)
    granted = _consent(db_session, _create_user(db_session, UserRole.client, "client-block-granted"))

    with pytest.raises(WhatsAppValidationError, match="Consentimiento"):
        WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient()).send_template(integration, _send_payload(revoked, approved, key="manual:test:revoked"), admin)
    with pytest.raises(WhatsAppValidationError, match="aprobada"):
        WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient()).send_template(integration, _send_payload(granted, draft, key="manual:test:draft"), admin)
    bad = _send_payload(granted, approved, key="manual:test:bad-vars")
    bad.variables.client_name = None
    with pytest.raises(WhatsAppValidationError, match="variables"):
        WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient()).send_template(integration, bad, admin)


def test_idempotency_and_failed_retry_reuse_message(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-idem")
    client_user = _create_user(db_session, UserRole.client, "client-idem")
    integration = _integration(db_session, admin)
    template = _template(db_session, integration)
    consent = _consent(db_session, client_user)
    service = WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient())
    first = service.send_template(integration, _send_payload(consent, template, key="manual:test:idempotent"), admin)
    second = service.send_template(integration, _send_payload(consent, template, key="manual:test:idempotent"), admin)
    assert second.skipped is True
    assert second.data.id == first.data.id

    failed = WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient(fail_code="rate_limit")).send_template(integration, _send_payload(consent, template, key="manual:test:failed"), admin)
    assert failed.success is False
    retried = WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient()).send_template(integration, _send_payload(consent, template, key="manual:test:failed"), admin)
    assert retried.data.id == failed.data.id
    assert retried.data.attempt == 2


def test_sync_updates_matching_templates_and_does_not_delete_local(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-sync")
    integration = _integration(db_session, admin)
    template = _template(db_session, integration, status=WhatsAppTemplateStatus.pending)
    fake = FakeWhatsAppCloudClient(templates=[WhatsAppRemoteTemplate(id="remote_1", name=template.name, language=template.language, category="UTILITY", status="APPROVED")])
    result = WhatsAppMessagingService(db_session, fake).sync_templates(integration, admin)
    db_session.refresh(template)
    assert result.updated_count == 1
    assert template.status == WhatsAppTemplateStatus.approved
    assert template.external_template_id == "remote_1"


def test_webhook_correlation_updates_monotonically_and_unknown_is_ignored(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-hook")
    client_user = _create_user(db_session, UserRole.client, "client-hook")
    integration = _integration(db_session, admin)
    template = _template(db_session, integration)
    consent = _consent(db_session, client_user)
    service = WhatsAppMessagingService(db_session, FakeWhatsAppCloudClient())
    sent = service.send_template(integration, _send_payload(consent, template, key="manual:test:webhook"), admin)
    message = db_session.get(WhatsAppMessage, sent.data.id)
    assert message is not None

    service.correlate_status(external_message_id=message.external_message_id, event_type=WhatsAppWebhookEventType.message_delivered, occurred_at=None)
    assert message.status == WhatsAppMessageStatus.delivered
    service.correlate_status(external_message_id=message.external_message_id, event_type=WhatsAppWebhookEventType.message_sent, occurred_at=None)
    assert message.status == WhatsAppMessageStatus.delivered
    count = db_session.query(WhatsAppMessage).count()
    service.correlate_status(external_message_id="unknown", event_type=WhatsAppWebhookEventType.message_read, occurred_at=None)
    assert db_session.query(WhatsAppMessage).count() == count


def test_admin_api_is_protected_and_safe(api_client: TestClient, db_session, monkeypatch) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-api")
    client = _create_user(db_session, UserRole.client, "client-api")
    professional = _create_user(db_session, UserRole.professional, "pro-api")
    integration = _integration(db_session, admin)
    template = _template(db_session, integration)
    consent = _consent(db_session, client)
    monkeypatch.setattr("app.whatsapp.messaging.HttpWhatsAppCloudClient", lambda: FakeWhatsAppCloudClient())

    payload = {
        "consent_id": consent.id,
        "template_id": template.id,
        "purpose": "appointment_confirmation",
        "language": "es_CL",
        "variables": {"client_name": "Cliente Demo"},
        "idempotency_key": "manual:test:api",
        "explicit_confirmation": True,
    }
    response = api_client.post(f"/api/v1/admin/integrations/{integration.id}/whatsapp/messages", json=payload, headers=_auth_headers(admin))
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["recipient_masked"] != consent.phone_e164
    assert "fake-token" not in response.text
    assert "Cliente Demo" not in response.text
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/whatsapp/messages", json={**payload, "token": "bad"}, headers=_auth_headers(admin)).status_code == 422
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/whatsapp/messages", json=payload).status_code == 401
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/whatsapp/messages", json=payload, headers=_auth_headers(client)).status_code == 403
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/whatsapp/messages", json=payload, headers=_auth_headers(professional)).status_code == 403
