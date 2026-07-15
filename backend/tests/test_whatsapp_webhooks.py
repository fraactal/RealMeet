import hashlib
import hmac
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.user import User, UserRole
from app.models.whatsapp import WhatsAppWebhookEvent
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService
from app.main import app


WEBHOOK_PATH = "/api/v1/integrations/whatsapp/webhook"


@pytest.fixture(autouse=True)
def webhook_settings(monkeypatch) -> None:
    monkeypatch.setattr(settings, "whatsapp_webhook_verify_token", "VERIFY_TOKEN_TEST")
    monkeypatch.setattr(settings, "whatsapp_app_secret", "APP_SECRET_TEST")
    monkeypatch.setattr(settings, "whatsapp_webhook_require_signature", True)
    monkeypatch.setattr(settings, "whatsapp_webhook_max_body_bytes", 4096)
    monkeypatch.setattr(settings, "whatsapp_webhook_event_retention_days", 30)
    monkeypatch.setattr(settings, "whatsapp_webhook_public_url", "https://example.test/api/v1/integrations/whatsapp/webhook")
    monkeypatch.setattr(settings, "whatsapp_phone_hmac_key", "PHONE_HMAC_TEST")
    monkeypatch.setattr(settings, "whatsapp_default_country_code", "CL")


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 13.1B%"))))
        if integration_ids:
            db.execute(delete(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name.in_(["Integration", "WhatsAppWebhook"])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        db.execute(delete(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.event_key.like("message:wamid.test%")))
        db.execute(delete(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.event_key.like("status:wamid.test%")))
        db.execute(delete(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.event_key.like("unknown:%")))
        db.execute(delete(AuditLog).where(AuditLog.entity_name == "WhatsAppWebhook"))
        db.execute(delete(User).where(User.email.like("test-13-1b-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _create_user(db, role: UserRole) -> User:
    user = User(
        email=f"test-13-1b-{role.value}-{uuid4().hex[:8]}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name=role.value.title(),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _whatsapp_config(phone_number_id: str = "987654321") -> dict:
    return {
        "waba_id": "123456789",
        "phone_number_id": phone_number_id,
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


def _create_integration(db, *, phone_number_id: str = "987654321", name: str | None = None) -> Integration:
    admin = _create_user(db, UserRole.admin)
    return IntegrationService(db).create_integration(
        IntegrationCreate(
            name=name or f"Test 13.1B WhatsApp {uuid4().hex[:6]}",
            integration_type=IntegrationType.messaging,
            provider=IntegrationProvider.whatsapp_cloud,
            config=_whatsapp_config(phone_number_id),
            secret_reference="WHATSAPP_ACCESS_TOKEN",
        ),
        admin,
    )


def _body(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _signature(raw: bytes, secret: str = "APP_SECRET_TEST") -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def _post(api_client: TestClient, payload: dict, signature: str | None = None):
    raw = _body(payload)
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-Hub-Signature-256"] = signature
    return api_client.post(WEBHOOK_PATH, content=raw, headers=headers)


def _message_payload(*, message_id: str = "wamid.test.message.1", phone_number_id: str = "987654321", text: str = "texto que no debe persistir") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry-test",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": phone_number_id, "display_phone_number": "+56999999999"},
                            "messages": [
                                {
                                    "from": "56912345678",
                                    "id": message_id,
                                    "timestamp": "1721000000",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _status_payload(status: str, *, message_id: str = "wamid.test.status.1", ts: str = "1721000001", phone_number_id: str = "987654321") -> dict:
    item = {"id": message_id, "status": status, "timestamp": ts, "recipient_id": "56912345678"}
    if status == "failed":
        item["errors"] = [{"code": 131000, "title": "Controlled failure"}]
    return {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"field": "messages", "value": {"metadata": {"phone_number_id": phone_number_id}, "statuses": [item]}}]}],
    }


def test_webhook_get_verification(api_client: TestClient, monkeypatch) -> None:
    ok = api_client.get(WEBHOOK_PATH, params={"hub.mode": "subscribe", "hub.verify_token": "VERIFY_TOKEN_TEST", "hub.challenge": "challenge-123"})
    assert ok.status_code == 200
    assert ok.text == "challenge-123"

    assert api_client.get(WEBHOOK_PATH, params={"hub.mode": "subscribe", "hub.verify_token": "bad", "hub.challenge": "challenge-123"}).status_code == 403
    assert api_client.get(WEBHOOK_PATH, params={"hub.mode": "other", "hub.verify_token": "VERIFY_TOKEN_TEST", "hub.challenge": "challenge-123"}).status_code == 400
    assert api_client.get(WEBHOOK_PATH, params={"hub.mode": "subscribe", "hub.verify_token": "VERIFY_TOKEN_TEST"}).status_code == 400
    monkeypatch.setattr(settings, "whatsapp_webhook_verify_token", None)
    missing = api_client.get(WEBHOOK_PATH, params={"hub.mode": "subscribe", "hub.verify_token": "any", "hub.challenge": "challenge-123"})
    assert missing.status_code == 503
    assert "VERIFY_TOKEN_TEST" not in missing.text


def test_webhook_signature_size_and_json(api_client: TestClient, db_session, monkeypatch) -> None:
    payload = _message_payload()
    raw = _body(payload)
    _create_integration(db_session)

    assert api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)}).status_code == 200
    assert api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": "sha256=bad"}).status_code == 403
    assert api_client.post(WEBHOOK_PATH, content=raw).status_code == 401
    assert api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": "md5=bad"}).status_code == 403
    tampered = _body(_message_payload(message_id="wamid.test.message.tampered"))
    assert api_client.post(WEBHOOK_PATH, content=tampered, headers={"X-Hub-Signature-256": _signature(raw)}).status_code == 403

    monkeypatch.setattr(settings, "whatsapp_webhook_require_signature", False)
    assert api_client.post(WEBHOOK_PATH, content=tampered).status_code == 200
    monkeypatch.setattr(settings, "whatsapp_webhook_require_signature", True)
    monkeypatch.setattr(settings, "whatsapp_webhook_max_body_bytes", 10)
    too_large = api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})
    assert too_large.status_code == 413
    monkeypatch.setattr(settings, "whatsapp_webhook_max_body_bytes", 4096)
    invalid = api_client.post(WEBHOOK_PATH, content=b"{", headers={"X-Hub-Signature-256": _signature(b"{")})
    assert invalid.status_code == 400
    empty = api_client.post(WEBHOOK_PATH, content=b"", headers={"X-Hub-Signature-256": _signature(b"")})
    assert empty.status_code == 400


def test_inbound_message_is_persisted_safely_and_deduplicated(api_client: TestClient, db_session) -> None:
    integration = _create_integration(db_session)
    payload = _message_payload(text="contenido privado")
    raw = _body(payload)

    first = api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})
    second = api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})

    assert first.status_code == 200
    assert first.json()["stored_count"] == 1
    assert second.status_code == 200
    assert second.json()["duplicate_count"] == 1

    events = list(db_session.scalars(select(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.integration_id == integration.id)))
    assert len(events) == 1
    event = events[0]
    assert event.event_type.value == "inbound_message"
    assert event.external_message_id == "wamid.test.message.1"
    assert event.received_count == 2
    assert event.duplicate is True
    assert "contenido privado" not in str(event.safe_metadata)
    assert "56912345678" not in str(event.safe_metadata)
    assert event.sender_phone_hash is not None


def test_status_events_are_distinct_and_failed_is_summarized(api_client: TestClient, db_session) -> None:
    integration = _create_integration(db_session)
    for status_value, ts in [("sent", "1721000001"), ("delivered", "1721000002"), ("read", "1721000003"), ("failed", "1721000004")]:
        raw = _body(_status_payload(status_value, ts=ts))
        response = api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})
        assert response.status_code == 200

    events = list(db_session.scalars(select(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.integration_id == integration.id)))
    assert {event.event_type.value for event in events} == {"message_sent", "message_delivered", "message_read", "message_failed"}
    failed = next(event for event in events if event.event_type.value == "message_failed")
    assert failed.error_code == "131000"
    assert failed.error_message == "Controlled failure"


def test_multiple_unknown_and_unresolved_events_are_safe(api_client: TestClient, db_session) -> None:
    _create_integration(db_session)
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {"field": "unknown_field", "value": {"metadata": {"phone_number_id": "000000000"}, "unexpected": {"nested": True}}},
                    {"field": "message_template_status_update", "value": {"message_template_id": "tmpl_1", "event": "APPROVED", "message_template_name": "demo"}},
                ]
            }
        ],
    }
    raw = _body(payload)
    response = api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})

    assert response.status_code == 200
    assert response.json()["received_count"] == 2
    events = list(db_session.scalars(select(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.payload_hash == hashlib.sha256(raw).hexdigest())))
    assert {event.event_type.value for event in events} == {"unknown", "template_status"}
    assert all(event.integration_id is None for event in events)
    assert "nested" not in str(events[0].safe_metadata)


def test_duplicate_integration_configuration_does_not_associate(api_client: TestClient, db_session) -> None:
    _create_integration(db_session, phone_number_id="111111111", name="Test 13.1B Duplicate A")
    _create_integration(db_session, phone_number_id="111111111", name="Test 13.1B Duplicate B")
    raw = _body(_message_payload(message_id="wamid.test.duplicate.config", phone_number_id="111111111"))
    response = api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})

    assert response.status_code == 200
    event = db_session.scalar(select(WhatsAppWebhookEvent).where(WhatsAppWebhookEvent.event_key == "message:wamid.test.duplicate.config"))
    assert event is not None
    assert event.integration_id is None
    assert event.safe_metadata["integration_resolution"] == "duplicate_configuration"


def test_admin_webhook_event_api_is_protected_and_safe(api_client: TestClient, db_session) -> None:
    integration = _create_integration(db_session)
    raw = _body(_message_payload(message_id="wamid.test.admin.safe"))
    api_client.post(WEBHOOK_PATH, content=raw, headers={"X-Hub-Signature-256": _signature(raw)})
    admin = _create_user(db_session, UserRole.admin)
    client = _create_user(db_session, UserRole.client)
    professional = _create_user(db_session, UserRole.professional)

    list_response = api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/webhook-events", headers=_auth_headers(admin))
    assert list_response.status_code == 200
    assert "body" not in list_response.text
    assert "56912345678" not in list_response.text
    assert "sha256=" not in list_response.text
    event_id = list_response.json()[0]["id"]

    detail = api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/webhook-events/{event_id}", headers=_auth_headers(admin))
    assert detail.status_code == 200
    assert "event_key_partial" in detail.json()
    assert "message:wamid.test.admin.safe" not in detail.text

    status_response = api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/webhook-status", headers=_auth_headers(admin))
    assert status_response.status_code == 200
    assert status_response.json()["public_url"] == "https://example.test/api/v1/integrations/whatsapp/webhook"
    assert status_response.json()["public_url_configured"] is True
    assert status_response.json()["app_secret_configured"] is True
    assert "APP_SECRET_TEST" not in status_response.text

    assert api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/webhook-events").status_code == 401
    assert api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/webhook-events", headers=_auth_headers(client)).status_code == 403
    assert api_client.get(f"/api/v1/admin/integrations/{integration.id}/whatsapp/webhook-events", headers=_auth_headers(professional)).status_code == 403
