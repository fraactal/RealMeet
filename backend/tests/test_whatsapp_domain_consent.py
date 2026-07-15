from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.user import User, UserRole
from app.models.whatsapp import WhatsAppConsent, WhatsAppTemplate
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService
from app.whatsapp.configuration import WhatsAppIntegrationConfig, validate_whatsapp_local_configuration
from app.whatsapp.enums import WhatsAppConsentPurpose, WhatsAppConsentStatus, WhatsAppTemplateStatus
from app.whatsapp.exceptions import WhatsAppValidationError
from app.whatsapp.phone import mask_phone_e164, normalize_phone, phone_hmac
from app.whatsapp.schemas import WhatsAppTemplateCreate
from app.main import app


@pytest.fixture(autouse=True)
def whatsapp_hmac_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "whatsapp_phone_hmac_key", "test-whatsapp-hmac-key")
    monkeypatch.setattr(settings, "whatsapp_default_country_code", "CL")


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 13.1A%"))))
        if integration_ids:
            db.execute(delete(WhatsAppTemplate).where(WhatsAppTemplate.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        user_ids = list(db.scalars(select(User.id).where(User.email.like("test-13-1a-%@realmeet.local"))))
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


def _create_user(db, role: UserRole, suffix: str | None = None) -> User:
    label = suffix or role.value
    user = User(
        email=f"test-13-1a-{label}-{uuid4().hex[:8]}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name=label.title(),
        role=role,
        phone="+56912345678",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _whatsapp_config(**overrides) -> dict:
    config = {
        "waba_id": "123456789",
        "phone_number_id": "987654321",
        "display_phone_number_masked": "+56 9 **** 5678",
        "graph_api_version": "v20.0",
        "default_language": "es_CL",
        "country_code": "CL",
        "secret_references": {
            "access_token": "WHATSAPP_ACCESS_TOKEN",
            "app_secret": "WHATSAPP_APP_SECRET",
            "verify_token": "WHATSAPP_WEBHOOK_VERIFY_TOKEN",
            "phone_hmac_key": "WHATSAPP_PHONE_HMAC_KEY",
        },
    }
    config.update(overrides)
    return config


def _create_whatsapp_integration(db, admin: User | None = None, **overrides) -> Integration:
    admin_user = admin or _create_user(db, UserRole.admin, "admin-int")
    payload = {
        "name": "Test 13.1A WhatsApp",
        "integration_type": IntegrationType.messaging,
        "provider": IntegrationProvider.whatsapp_cloud,
        "config": _whatsapp_config(),
        "secret_reference": "WHATSAPP_ACCESS_TOKEN",
    }
    payload.update(overrides)
    return IntegrationService(db).create_integration(IntegrationCreate(**payload), admin_user)


def test_backend_settings_start_without_whatsapp_variables() -> None:
    assert settings.whatsapp_cloud_enabled is False
    assert settings.whatsapp_access_token is None


def test_whatsapp_config_accepts_valid_payload_and_rejects_invalid_values() -> None:
    assert WhatsAppIntegrationConfig(**_whatsapp_config()).waba_id == "123456789"

    with pytest.raises(ValidationError):
        WhatsAppIntegrationConfig(**_whatsapp_config(waba_id="abc"))
    with pytest.raises(ValidationError):
        WhatsAppIntegrationConfig(**_whatsapp_config(phone_number_id="abc"))
    with pytest.raises(ValidationError):
        WhatsAppIntegrationConfig(**_whatsapp_config(default_language="invalid_language_value"))
    with pytest.raises(ValidationError):
        WhatsAppIntegrationConfig(**_whatsapp_config(token="do-not-store"))


def test_integration_create_rejects_wrong_provider_type_and_keeps_whatsapp_non_operational(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-provider")
    with pytest.raises(ValidationError):
        IntegrationCreate(name="Test 13.1A Wrong", integration_type=IntegrationType.automation, provider=IntegrationProvider.whatsapp_cloud, config=_whatsapp_config())

    integration = _create_whatsapp_integration(db_session, admin)
    assert integration.status == IntegrationStatus.configured
    result = validate_whatsapp_local_configuration(integration)
    assert result["metadata"]["operational_for_sending"] is False


def test_phone_normalization_masking_and_hmac(monkeypatch) -> None:
    normalized = normalize_phone("9 1234 5678", default_country_code="CL")
    assert normalized.e164 == "+56912345678"
    assert normalized.masked == "+56 9 **** 5678"
    assert mask_phone_e164("+56912345678") == "+56 9 **** 5678"
    assert phone_hmac(normalized.e164, key="one") == phone_hmac(normalized.e164, key="one")
    assert phone_hmac(normalized.e164, key="one") != phone_hmac(normalized.e164, key="two")

    monkeypatch.setattr(settings, "whatsapp_default_country_code", None)
    with pytest.raises(WhatsAppValidationError):
        normalize_phone("912345678", default_country_code=None)
    with pytest.raises(WhatsAppValidationError):
        normalize_phone("+56 9 ABC 5678")
    with pytest.raises(WhatsAppValidationError):
        phone_hmac("+56912345678", key="")


def test_user_consent_grant_list_and_revoke(api_client: TestClient, db_session) -> None:
    client_user = _create_user(db_session, UserRole.client, "client-consent")
    headers = _auth_headers(client_user)

    payload = {
        "phone": "9 1234 5678",
        "purpose": "appointment_reminders",
        "consent_text_version": "wa-consent-v1",
        "explicit_confirmation": True,
    }
    grant_response = api_client.post("/api/v1/users/me/whatsapp-consents", json=payload, headers=headers)
    assert grant_response.status_code == 200
    assert grant_response.json()["phone_masked"] == "+56 9 **** 5678"
    assert grant_response.json()["status"] == "granted"
    assert "phone_hash" not in grant_response.text

    list_response = api_client.get("/api/v1/users/me/whatsapp-consents", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    revoke_response = api_client.delete("/api/v1/users/me/whatsapp-consents/appointment_reminders", headers=headers)
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    consent = db_session.get(WhatsAppConsent, grant_response.json()["id"])
    assert consent.status == WhatsAppConsentStatus.revoked


def test_consent_purposes_are_separate_and_audit_is_safe(api_client: TestClient, db_session) -> None:
    client_user = _create_user(db_session, UserRole.client, "client-audit")
    headers = _auth_headers(client_user)
    for purpose in ("appointment_transactional", "appointment_updates"):
        response = api_client.post(
            "/api/v1/users/me/whatsapp-consents",
            json={"phone": "+56912345678", "purpose": purpose, "consent_text_version": "v1", "explicit_confirmation": True},
            headers=headers,
        )
        assert response.status_code == 200

    list_response = api_client.get("/api/v1/users/me/whatsapp-consents", headers=headers)
    assert len(list_response.json()) == 2

    logs = list(db_session.scalars(select(AuditLog).where(AuditLog.action == "whatsapp_consent_granted")))
    assert logs
    assert "+56912345678" not in str([log.metadata_json for log in logs])
    assert "phone_hash" not in str([log.metadata_json for log in logs])


def test_admin_consent_summary_masks_phone_and_professional_is_forbidden(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-consents")
    professional = _create_user(db_session, UserRole.professional, "pro-consents")
    client_user = _create_user(db_session, UserRole.client, "client-summary")

    correction = api_client.post(
        "/api/v1/admin/whatsapp/consents/corrections",
        json={
            "user_id": client_user.id,
            "phone": "+56912345678",
            "purpose": "appointment_transactional",
            "consent_text_version": "admin-v1",
            "reason": "Correccion documentada por solicitud del usuario",
        },
        headers=_auth_headers(admin),
    )
    assert correction.status_code == 200

    summary = api_client.get("/api/v1/admin/whatsapp/consents", headers=_auth_headers(admin))
    assert summary.status_code == 200
    assert "+56912345678" not in summary.text
    assert "+56 9 **** 5678" in summary.text

    forbidden = api_client.get("/api/v1/admin/whatsapp/consents", headers=_auth_headers(professional))
    assert forbidden.status_code == 403


def test_whatsapp_template_lifecycle_and_validation(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-template")
    integration = _create_whatsapp_integration(db_session, admin, name="Test 13.1A Template")
    headers = _auth_headers(admin)

    status_response = api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/status", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["operational_for_sending"] is False

    create_response = api_client.post(
        f"/api/v1/admin/integrations/{integration.id}/whatsapp/templates",
        json={
            "name": "appointment_confirmation",
            "language": "es_CL",
            "category": "utility",
            "purpose": "appointment_confirmation",
            "components_schema": {"variables": [{"key": "client_name", "required": True, "sensitive": False}]},
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    assert create_response.json()["status"] == WhatsAppTemplateStatus.draft.value
    template_id = create_response.json()["id"]

    update_response = api_client.patch(
        f"/api/v1/admin/integrations/{integration.id}/whatsapp/templates/{template_id}",
        json={"components_schema": {"variables": [{"key": "appointment_date", "required": True, "sensitive": False}]}},
        headers=headers,
    )
    assert update_response.status_code == 200

    rejected_variable = api_client.post(
        f"/api/v1/admin/integrations/{integration.id}/whatsapp/templates",
        json={
            "name": "bad_variable",
            "language": "es_CL",
            "category": "utility",
            "purpose": "appointment_confirmation",
            "components_schema": {"variables": [{"key": "diagnosis", "required": True, "sensitive": False}]},
        },
        headers=headers,
    )
    assert rejected_variable.status_code == 422

    rejected_marketing = api_client.post(
        f"/api/v1/admin/integrations/{integration.id}/whatsapp/templates",
        json={"name": "marketing", "language": "es_CL", "category": "marketing", "purpose": "appointment_confirmation"},
        headers=headers,
    )
    assert rejected_marketing.status_code == 422

    rejected_status = api_client.post(
        f"/api/v1/admin/integrations/{integration.id}/whatsapp/templates",
        json={"name": "approved_attempt", "language": "es_CL", "category": "utility", "purpose": "appointment_confirmation", "status": "approved"},
        headers=headers,
    )
    assert rejected_status.status_code == 422


def test_template_schema_rejects_fields_extra() -> None:
    with pytest.raises(ValidationError):
        WhatsAppTemplateCreate(name="x", language="es_CL", category="utility", purpose="meeting_ready", external_template_id="remote")


def test_whatsapp_template_rejects_wrong_provider(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin-wrong-provider")
    mock = IntegrationService(db_session).create_integration(
        IntegrationCreate(
            name="Test 13.1A Mock",
            integration_type=IntegrationType.automation,
            provider=IntegrationProvider.mock,
            config={"simulate_error": False, "health": "healthy", "response_delay_ms": 0},
            secret_reference="MOCK_INTEGRATION_SECRET",
        ),
        admin,
    )
    response = api_client.get(f"/api/v1/admin/integrations/{mock.id}/whatsapp/templates", headers=_auth_headers(admin))
    assert response.status_code == 422
