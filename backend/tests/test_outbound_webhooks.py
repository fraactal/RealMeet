from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.automation.client import FakeOutboundWebhookClient
from app.automation.contracts import DomainEvent
from app.automation.enums import WebhookDeliveryStatus, WebhookEventType
from app.automation.schemas import WebhookSubscriptionCreate
from app.automation.service import DomainEventPublisher, WebhookDeliveryService, sign_payload, validate_target_url
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.main import app
from app.models.appointment import AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.user import User, UserRole
from app.models.webhook import WebhookDelivery, WebhookSubscription


@pytest.fixture()
def db_session(monkeypatch: pytest.MonkeyPatch) -> Iterator:
    monkeypatch.setenv("REALMEET_WEBHOOK_SECRET", "test-webhook-secret")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        subscription_ids = list(db.scalars(select(WebhookSubscription.id).where(WebhookSubscription.name.like("Test 14.1%"))))
        if subscription_ids:
            db.execute(delete(WebhookDelivery).where(WebhookDelivery.subscription_id.in_(subscription_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name.in_(["WebhookSubscription", "WebhookDelivery"])))
            db.execute(delete(WebhookSubscription).where(WebhookSubscription.id.in_(subscription_ids)))
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 14.1%"))))
        if integration_ids:
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        db.execute(delete(User).where(User.email.like("test-14-1-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-14-1-{suffix}-{role.value}@realmeet.local",
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


def _integration(db, provider: IntegrationProvider = IntegrationProvider.generic_webhook) -> Integration:
    item = Integration(
        name=f"Test 14.1 {provider.value}",
        integration_type=IntegrationType.webhook,
        provider=provider,
        enabled=False,
        status=IntegrationStatus.configured,
        config={},
        secret_reference=None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _subscription(db, *, enabled: bool = True, client: FakeOutboundWebhookClient | None = None) -> tuple[WebhookDeliveryService, WebhookSubscription]:
    service = WebhookDeliveryService(db, client or FakeOutboundWebhookClient())
    actor = _create_user(db, UserRole.admin, "subscription")
    item = service.create_subscription(
        WebhookSubscriptionCreate(
            integration_id=_integration(db).id,
            name="Test 14.1 Subscription",
            target_url="http://localhost:9999/webhook",
            event_types=[WebhookEventType.appointment_created, WebhookEventType.appointment_cancelled, WebhookEventType.webhook_test],
            secret_reference="REALMEET_WEBHOOK_SECRET",
        ),
        actor,
    )
    if enabled:
        item = service.set_enabled(item.id, True, actor)
    return service, item


def _event(event_type: WebhookEventType = WebhookEventType.appointment_created) -> DomainEvent:
    return DomainEvent.create(
        event_type=event_type,
        entity_type="appointment",
        entity_id=123,
        correlation_id="appointment:123",
        payload={
            "appointment_id": 123,
            "status": "pending",
            "starts_at": datetime.now(UTC).isoformat(),
            "professional_id": 4,
            "client_id": 8,
            "modality": "online",
        },
    )


def _appointment(appointment_id: int = 123, status: AppointmentStatus = AppointmentStatus.pending):
    return SimpleNamespace(
        id=appointment_id,
        status=status,
        start_datetime=datetime.now(UTC) + timedelta(days=1),
        professional_id=4,
        client_id=8,
        consultation_mode=SimpleNamespace(value="online"),
    )


def test_admin_creates_valid_subscription(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "api-admin")
    integration = _integration(db_session)

    response = api_client.post(
        "/api/v1/admin/webhook-subscriptions",
        headers=_auth_headers(admin),
        json={
            "integration_id": integration.id,
            "name": "Test 14.1 API",
            "target_url": "http://localhost:9999/webhook",
            "event_types": ["appointment.created"],
            "secret_reference": "REALMEET_WEBHOOK_SECRET",
        },
    )

    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_insecure_url_and_direct_secret_are_rejected(db_session) -> None:
    with pytest.raises(Exception):
        validate_target_url("ftp://example.com/hook", app_env=settings.app_env)

    with pytest.raises(ValueError):
        WebhookSubscriptionCreate(
            integration_id=_integration(db_session).id,
            name="Test 14.1 Bad Secret",
            target_url="https://example.com/hook",
            event_types=[WebhookEventType.appointment_created],
            secret_reference="plain-secret-value",
        )


def test_signature_hmac_is_stable_and_correct() -> None:
    payload = {"event_id": "evt_1", "payload": {"appointment_id": 123}}
    signature = sign_payload(payload, secret="secret", timestamp="2026-07-15T00:00:00+00:00")

    assert signature.startswith("sha256=")
    assert signature == sign_payload(payload, secret="secret", timestamp="2026-07-15T00:00:00+00:00")
    assert signature != sign_payload(payload, secret="other", timestamp="2026-07-15T00:00:00+00:00")


def test_fake_delivery_success_and_idempotency(db_session) -> None:
    fake = FakeOutboundWebhookClient()
    service, subscription = _subscription(db_session, client=fake)
    event = _event()

    first = service.deliver_to_subscription(subscription, event)
    second = service.deliver_to_subscription(subscription, event)

    assert first.id == second.id
    assert first.status == WebhookDeliveryStatus.succeeded
    assert len(fake.calls) == 1


def test_fake_delivery_failure_and_manual_retry(db_session) -> None:
    failing = FakeOutboundWebhookClient(should_fail=True, status_code=500)
    service, subscription = _subscription(db_session, client=failing)
    delivery = service.deliver_to_subscription(subscription, _event())
    assert delivery.status == WebhookDeliveryStatus.failed

    retry_service = WebhookDeliveryService(db_session, FakeOutboundWebhookClient())
    actor = _create_user(db_session, UserRole.admin, "retry")
    retried = retry_service.retry_delivery(delivery.id, actor)

    assert retried.id == delivery.id
    assert retried.status == WebhookDeliveryStatus.succeeded
    assert retried.attempt == 2


def test_appointment_created_generates_delivery_and_failure_does_not_corrupt_reservation_context(db_session) -> None:
    failing = FakeOutboundWebhookClient(should_fail=True, status_code=503)
    service, _ = _subscription(db_session, client=failing)

    deliveries = DomainEventPublisher(db_session, service).publish_appointment_created(_appointment())

    assert len(deliveries) == 1
    assert deliveries[0].status == WebhookDeliveryStatus.failed
    assert _appointment().status == AppointmentStatus.pending


def test_appointment_cancelled_generates_delivery(db_session) -> None:
    fake = FakeOutboundWebhookClient()
    service, _ = _subscription(db_session, client=fake)

    deliveries = DomainEventPublisher(db_session, service).publish_appointment_cancelled(_appointment(status=AppointmentStatus.cancelled))

    assert len(deliveries) == 1
    assert deliveries[0].event_type == "appointment.cancelled"
    assert deliveries[0].status == WebhookDeliveryStatus.succeeded


def test_client_and_professional_are_forbidden_and_admin_allowed(api_client: TestClient, db_session) -> None:
    client = _create_user(db_session, UserRole.client, "role-client")
    professional = _create_user(db_session, UserRole.professional, "role-professional")
    admin = _create_user(db_session, UserRole.admin, "role-admin")

    assert api_client.get("/api/v1/admin/webhook-subscriptions", headers=_auth_headers(client)).status_code == 403
    assert api_client.get("/api/v1/admin/webhook-subscriptions", headers=_auth_headers(professional)).status_code == 403
    assert api_client.get("/api/v1/admin/webhook-subscriptions", headers=_auth_headers(admin)).status_code == 200
