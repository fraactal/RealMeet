import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.automation.enums import WebhookEventType
from app.automation.examples import EXAMPLES, EXAMPLES_DIR
from app.automation.payloads import AutomationPayloadBuilder
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.execute(delete(User).where(User.email.like("test-14-3-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-14-3-{suffix}-{role.value}@realmeet.local",
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


def _auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _appointment():
    professional_user = SimpleNamespace(first_name="Profesional", last_name="RealMeet", email="pro@example.com", phone="+56911112222")
    client_user = SimpleNamespace(first_name="Cliente", last_name="RealMeet", email="cliente@example.com", phone="+56912345678")
    return SimpleNamespace(
        id=143,
        status=SimpleNamespace(value="confirmed"),
        start_datetime=datetime.now(UTC) + timedelta(days=2),
        end_datetime=datetime.now(UTC) + timedelta(days=2, hours=1),
        professional_id=45,
        client_id=67,
        professional=SimpleNamespace(id=45, user=professional_user),
        client=SimpleNamespace(id=67, user=client_user),
        cancellation_reason=None,
    )


def _contains_sensitive_key(payload: dict) -> bool:
    sensitive = {"secret", "token", "password", "credential"}
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if any(item in key.lower() for item in sensitive):
                    return True
                if isinstance(value, dict):
                    stack.append(value)
                elif isinstance(value, list):
                    stack.extend(item for item in value if isinstance(item, dict))
    return False


def test_builder_generates_appointment_created_payload_with_schema_and_masked_phone() -> None:
    payload = AutomationPayloadBuilder().build(
        WebhookEventType.appointment_created,
        _appointment(),
        event_id="evt_143",
        occurred_at=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
    )

    assert payload["schema_version"] == "1.0"
    assert payload["event_type"] == "appointment.created"
    assert payload["event_id"] == "evt_143"
    assert payload["appointment"]["id"] == 143
    assert payload["client"]["email"] == "cliente@example.com"
    assert payload["client"]["phone"].endswith("5678")
    assert "*" in payload["client"]["phone"]
    assert not _contains_sensitive_key(payload)


def test_builder_generates_summarized_notification_failed_payload() -> None:
    notification = SimpleNamespace(
        id=55,
        appointment_id=143,
        channel=SimpleNamespace(value="whatsapp"),
        status=SimpleNamespace(value="failed"),
        event_type=SimpleNamespace(value="appointment_reminder"),
        error_code="provider_timeout",
        error_message="full provider response must not be exposed",
    )

    payload = AutomationPayloadBuilder().build(
        WebhookEventType.notification_failed,
        notification,
        event_id="evt_notification_failed",
        occurred_at=datetime(2026, 7, 15, 12, 5, tzinfo=UTC),
    )

    assert payload["schema_version"] == "1.0"
    assert payload["notification"]["channel"] == "whatsapp"
    assert payload["notification"]["status"] == "failed"
    assert payload["notification"]["error_code"] == "provider_timeout"
    assert "error_message" not in payload["notification"]


def test_admin_can_list_examples_and_get_valid_workflow_json(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "examples-admin")

    response = api_client.get("/api/v1/admin/automation/examples", headers=_auth_headers(admin))
    assert response.status_code == 200
    assert {item["key"] for item in response.json()} == {example.key for example in EXAMPLES}

    detail = api_client.get("/api/v1/admin/automation/examples/google_sheets_appointment_log", headers=_auth_headers(admin))
    assert detail.status_code == 200
    assert detail.json()["example"]["workflow_filename"] == "realmeet-google-sheets-appointments.json"
    assert detail.json()["workflow"]["active"] is False


def test_admin_integrations_list_returns_page_contract(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "integrations-list-admin")

    response = api_client.get("/api/v1/admin/integrations", headers=_auth_headers(admin))

    assert response.status_code == 200
    assert "items" in response.json()
    assert "meta" in response.json()


def test_unknown_example_returns_404(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "missing-admin")

    response = api_client.get("/api/v1/admin/automation/examples/unknown", headers=_auth_headers(admin))

    assert response.status_code == 404


def test_client_and_professional_cannot_access_examples(api_client: TestClient, db_session) -> None:
    client = _create_user(db_session, UserRole.client, "role-client")
    professional = _create_user(db_session, UserRole.professional, "role-professional")

    assert api_client.get("/api/v1/admin/automation/examples", headers=_auth_headers(client)).status_code == 403
    assert api_client.get("/api/v1/admin/automation/examples", headers=_auth_headers(professional)).status_code == 403


def test_workflow_json_files_parse_and_catalog_references_existing_files() -> None:
    filenames = {example.workflow_filename for example in EXAMPLES}
    assert filenames == {
        "realmeet-google-sheets-appointments.json",
        "realmeet-generic-crm-upsert.json",
        "realmeet-internal-failure-notification.json",
    }

    for filename in filenames:
        path = EXAMPLES_DIR / filename
        assert path.is_file()
        with path.open("r", encoding="utf-8") as file:
            workflow = json.load(file)
        assert workflow["nodes"]
        assert workflow["active"] is False
