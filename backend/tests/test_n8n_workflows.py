from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.automation.client import FakeOutboundWebhookClient
from app.automation.contracts import DomainEvent
from app.automation.enums import WebhookDeliveryStatus, WebhookEventType
from app.automation.n8n import N8nWorkflowService, validate_n8n_config, validate_webhook_path
from app.automation.n8n_schemas import N8nWorkflowCreate
from app.automation.service import DomainEventPublisher, WebhookDeliveryService
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.main import app
from app.models.appointment import AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.n8n import N8nWorkflow
from app.models.user import User, UserRole
from app.models.webhook import WebhookDelivery, WebhookSubscription


@pytest.fixture()
def db_session(monkeypatch: pytest.MonkeyPatch) -> Iterator:
    monkeypatch.setenv("REALMEET_N8N_WEBHOOK_SECRET", "test-n8n-secret")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        workflow_ids = list(db.scalars(select(N8nWorkflow.id).where(N8nWorkflow.name.like("Test 14.2%"))))
        subscription_ids = list(db.scalars(select(N8nWorkflow.subscription_id).where(N8nWorkflow.name.like("Test 14.2%"))))
        if subscription_ids:
            db.execute(delete(WebhookDelivery).where(WebhookDelivery.subscription_id.in_(subscription_ids)))
        if workflow_ids:
            db.execute(delete(N8nWorkflow).where(N8nWorkflow.id.in_(workflow_ids)))
        if subscription_ids:
            db.execute(delete(AuditLog).where(AuditLog.entity_name.in_(["WebhookSubscription", "WebhookDelivery"])))
            db.execute(delete(WebhookSubscription).where(WebhookSubscription.id.in_(subscription_ids)))
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 14.2%"))))
        if integration_ids:
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        db.execute(delete(User).where(User.email.like("test-14-2-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-14-2-{suffix}-{role.value}@realmeet.local",
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


def _integration(db) -> Integration:
    item = Integration(
        name="Test 14.2 n8n",
        integration_type=IntegrationType.automation,
        provider=IntegrationProvider.n8n,
        enabled=False,
        status=IntegrationStatus.configured,
        config={"base_url": "http://localhost:9999", "environment": "test"},
        secret_reference="REALMEET_N8N_WEBHOOK_SECRET",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _workflow_payload(event_types: list[WebhookEventType] | None = None) -> N8nWorkflowCreate:
    return N8nWorkflowCreate(
        name="Test 14.2 Workflow",
        description="Workflow de prueba n8n",
        webhook_path="webhook/realmeet",
        event_types=event_types or [WebhookEventType.appointment_created],
        secret_reference="REALMEET_N8N_WEBHOOK_SECRET",
    )


def _appointment(appointment_id: int = 142, status: AppointmentStatus = AppointmentStatus.pending):
    return SimpleNamespace(
        id=appointment_id,
        status=status,
        start_datetime=datetime.now(UTC) + timedelta(days=1),
        professional_id=4,
        client_id=8,
        consultation_mode=SimpleNamespace(value="online"),
    )


def _service(db, fake: FakeOutboundWebhookClient | None = None) -> N8nWorkflowService:
    return N8nWorkflowService(db, WebhookDeliveryService(db, fake or FakeOutboundWebhookClient()))


def test_admin_creates_valid_n8n_integration(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "api-admin")

    response = api_client.post(
        "/api/v1/admin/integrations",
        headers=_auth_headers(admin),
        json={
            "name": "Test 14.2 API n8n",
            "integration_type": "automation",
            "provider": "n8n",
            "config": {"base_url": "http://localhost:9999", "environment": "test"},
            "secret_reference": "REALMEET_N8N_WEBHOOK_SECRET",
        },
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "n8n"
    assert response.json()["status"] == "configured"


def test_insecure_base_url_and_invalid_path_are_rejected() -> None:
    with pytest.raises(Exception):
        validate_n8n_config({"base_url": "http://example.com", "environment": "test"})

    with pytest.raises(ValueError):
        validate_webhook_path("../webhook")

    assert settings.app_env


def test_create_and_enable_workflow(db_session) -> None:
    actor = _create_user(db_session, UserRole.admin, "workflow-admin")
    integration = _integration(db_session)
    service = _service(db_session)

    workflow = service.create_workflow(integration.id, _workflow_payload(), actor)
    assert workflow.enabled is False
    assert workflow.subscription_id is not None

    enabled = service.set_enabled(integration.id, workflow.id, True, actor)
    subscription = db_session.get(WebhookSubscription, enabled.subscription_id)
    assert enabled.enabled is True
    assert subscription.enabled is True


def test_allowed_event_creates_delivery_and_unsubscribed_event_does_not(db_session) -> None:
    actor = _create_user(db_session, UserRole.admin, "events-admin")
    integration = _integration(db_session)
    fake = FakeOutboundWebhookClient()
    service = _service(db_session, fake)
    workflow = service.create_workflow(integration.id, _workflow_payload([WebhookEventType.appointment_cancelled]), actor)
    service.set_enabled(integration.id, workflow.id, True, actor)

    none = DomainEventPublisher(db_session, service.webhook_service).publish_appointment_created(_appointment())
    assert none == []

    deliveries = DomainEventPublisher(db_session, service.webhook_service).publish_appointment_cancelled(_appointment(status=AppointmentStatus.cancelled))
    assert len(deliveries) == 1
    assert deliveries[0].status == WebhookDeliveryStatus.succeeded


def test_manual_test_uses_fake_delivery_and_idempotency_avoids_duplicate(db_session) -> None:
    actor = _create_user(db_session, UserRole.admin, "test-admin")
    integration = _integration(db_session)
    fake = FakeOutboundWebhookClient()
    service = _service(db_session, fake)
    workflow = service.create_workflow(integration.id, _workflow_payload(), actor)
    service.set_enabled(integration.id, workflow.id, True, actor)

    test_delivery = service.test_workflow(integration.id, workflow.id, actor)
    assert test_delivery.event_type == "n8n.workflow.test"
    assert test_delivery.status == WebhookDeliveryStatus.succeeded

    event = DomainEvent.create(
        event_type=WebhookEventType.appointment_created,
        entity_type="appointment",
        entity_id=142,
        correlation_id="appointment:142",
        payload={"appointment_id": 142, "status": "pending"},
    )
    subscription = db_session.get(WebhookSubscription, workflow.subscription_id)
    first = service.webhook_service.deliver_to_subscription(subscription, event)
    second = service.webhook_service.deliver_to_subscription(subscription, event)

    assert first.id == second.id
    assert len(fake.calls) == 2


def test_client_and_professional_are_forbidden_and_admin_allowed(api_client: TestClient, db_session) -> None:
    integration = _integration(db_session)
    client = _create_user(db_session, UserRole.client, "role-client")
    professional = _create_user(db_session, UserRole.professional, "role-professional")
    admin = _create_user(db_session, UserRole.admin, "role-admin")
    path = f"/api/v1/admin/integrations/{integration.id}/n8n/workflows"

    assert api_client.get(path, headers=_auth_headers(client)).status_code == 403
    assert api_client.get(path, headers=_auth_headers(professional)).status_code == 403
    assert api_client.get(path, headers=_auth_headers(admin)).status_code == 200
