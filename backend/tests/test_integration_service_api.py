from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import (
    IntegrationConfigurationError,
    IntegrationOperationUnsupportedError,
    IntegrationProviderExecutionError,
    IntegrationProviderUnsupportedError,
)
from app.integrations.providers.mock import MockIntegrationProvider
from app.integrations.registry import provider_registry
from app.main import app
from app.models.audit_log import AuditLog
from app.models.integration import Integration, IntegrationExecution
from app.models.user import User, UserRole
from app.schemas.integrations import IntegrationCreate, IntegrationUpdate
from app.services.integrations import IntegrationService


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 11.2%"))))
        if integration_ids:
            db.execute(delete(IntegrationExecution).where(IntegrationExecution.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        db.execute(delete(User).where(User.email.like("test-11-2-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _create_user(db, role: UserRole) -> User:
    user = User(
        email=f"test-11-2-{role.value}@realmeet.local",
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


def _integration_payload(**overrides) -> dict:
    payload = {
        "name": "Test 11.2 Mock",
        "integration_type": "automation",
        "provider": "mock",
        "config": {"simulate_error": False, "health": "healthy", "response_delay_ms": 0},
        "secret_reference": "MOCK_INTEGRATION_SECRET",
    }
    payload.update(overrides)
    return payload


def _create_integration(db, *, name: str = "Test 11.2 Mock", provider: IntegrationProvider = IntegrationProvider.mock, config: dict | None = None) -> Integration:
    service = IntegrationService(db)
    admin = _create_user(db, UserRole.admin)
    return service.create_integration(
        IntegrationCreate(
            name=name,
            integration_type=IntegrationType.automation,
            provider=provider,
            config=config if config is not None else {"simulate_error": False, "health": "healthy", "response_delay_ms": 0},
            secret_reference="MOCK_INTEGRATION_SECRET",
        ),
        admin,
    )


def test_registry_resolves_mock_and_rejects_future_provider() -> None:
    assert provider_registry.get(IntegrationProvider.mock).provider == "mock"
    assert provider_registry.get(IntegrationProvider.google_meet).provider == "google_meet"

    with pytest.raises(IntegrationProviderUnsupportedError):
        provider_registry.get(IntegrationProvider.twilio)


def test_mock_provider_validates_config_and_rejects_invalid_config(db_session) -> None:
    integration = _create_integration(db_session, name="Test 11.2 Provider Valid")
    provider = MockIntegrationProvider()

    assert provider.validate_configuration(integration).success is True

    integration.config = {"unknown": True}
    with pytest.raises(IntegrationConfigurationError):
        provider.validate_configuration(integration)


def test_mock_provider_health_and_simulated_error(db_session) -> None:
    integration = _create_integration(db_session, name="Test 11.2 Provider Health")
    provider = MockIntegrationProvider()

    assert provider.health_check(integration).success is True

    integration.config = {"simulate_error": True}
    with pytest.raises(IntegrationProviderExecutionError):
        provider.health_check(integration)


def test_mock_provider_executes_safe_test_operation(db_session) -> None:
    integration = _create_integration(db_session, name="Test 11.2 Provider Execute")
    result = MockIntegrationProvider().execute(integration, "test", payload={"ignored": "safe"})

    assert result.success is True
    assert result.metadata == {"provider": "mock", "operation": "test"}


def test_service_creates_updates_validates_enables_and_disables(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    service = IntegrationService(db_session)

    integration = service.create_integration(IntegrationCreate(**_integration_payload(name="Test 11.2 Service")), admin)
    assert integration.enabled is False
    assert integration.status == IntegrationStatus.configured

    updated = service.update_integration(integration.id, IntegrationUpdate(name="Test 11.2 Service Updated"), admin)
    assert updated.name == "Test 11.2 Service Updated"

    result = service.validate_configuration(integration.id, admin)
    assert result.success is True

    enabled = service.enable_integration(integration.id, admin)
    assert enabled.enabled is True

    disabled = service.disable_integration(integration.id, admin)
    assert disabled.enabled is False


def test_service_rejects_enable_for_future_provider(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    service = IntegrationService(db_session)
    integration = service.create_integration(
        IntegrationCreate(**_integration_payload(name="Test 11.2 Future", provider="google_meet", config={})),
        admin,
    )

    with pytest.raises(IntegrationOperationUnsupportedError):
        service.enable_integration(integration.id, admin)


def test_health_check_records_execution_and_failure_updates_error(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    service = IntegrationService(db_session)
    integration = service.create_integration(IntegrationCreate(**_integration_payload(name="Test 11.2 Health")), admin)
    service.enable_integration(integration.id, admin)

    result = service.health_check(integration.id, admin, idempotency_key="test-11-2:health")
    assert result.success is True
    assert result.execution_id is not None

    service.update_integration(integration.id, IntegrationUpdate(config={"simulate_error": True}), admin)
    service.enable_integration(integration.id, admin)
    failed = service.health_check(integration.id, admin, idempotency_key="test-11-2:health-failed")
    assert failed.success is False
    refreshed = service.get_integration(integration.id)
    assert refreshed.status == IntegrationStatus.error
    assert refreshed.last_error_message == "Health check mock fallo de forma simulada"


def test_test_mock_idempotency_and_failed_retry(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    service = IntegrationService(db_session)
    integration = service.create_integration(IntegrationCreate(**_integration_payload(name="Test 11.2 Idempotency")), admin)
    service.enable_integration(integration.id, admin)

    first = service.test_integration(integration.id, admin, idempotency_key="test-11-2:test")
    second = service.test_integration(integration.id, admin, idempotency_key="test-11-2:test")
    assert first.success is True
    assert second.skipped is True

    service.update_integration(integration.id, IntegrationUpdate(config={"simulate_error": True}), admin)
    service.enable_integration(integration.id, admin)
    failed = service.test_integration(integration.id, admin, idempotency_key="test-11-2:retry")
    assert failed.success is False
    execution = service.executions.get_by_idempotency_key(integration.id, "test-11-2:retry")
    assert execution is not None
    assert execution.status == IntegrationExecutionStatus.failed

    service.update_integration(integration.id, IntegrationUpdate(config={"simulate_error": False}), admin)
    service.enable_integration(integration.id, admin)
    retried = service.test_integration(integration.id, admin, idempotency_key="test-11-2:retry")
    assert retried.success is True
    db_session.refresh(execution)
    assert execution.attempt == 2


def test_audit_log_does_not_store_secrets(db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = IntegrationService(db_session).create_integration(IntegrationCreate(**_integration_payload(name="Test 11.2 Audit")), admin)

    logs = list(db_session.scalars(select(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id == str(integration.id))))

    assert logs
    assert all("secret_reference" not in (log.metadata_json or {}) for log in logs)
    assert all("MOCK_INTEGRATION_SECRET" not in str(log.metadata_json) for log in logs)


def test_admin_api_lifecycle_and_idempotency(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    headers = _auth_headers(admin)

    list_response = api_client.get("/api/v1/admin/integrations", headers=headers)
    assert list_response.status_code == 200

    create_response = api_client.post("/api/v1/admin/integrations", json=_integration_payload(name="Test 11.2 API"), headers=headers)
    assert create_response.status_code == 200
    integration_id = create_response.json()["id"]
    assert create_response.json()["enabled"] is False

    update_response = api_client.patch(
        f"/api/v1/admin/integrations/{integration_id}",
        json={"name": "Test 11.2 API Updated"},
        headers=headers,
    )
    assert update_response.status_code == 200

    validate_response = api_client.post(f"/api/v1/admin/integrations/{integration_id}/validate", headers=headers)
    assert validate_response.status_code == 200

    enable_response = api_client.post(f"/api/v1/admin/integrations/{integration_id}/enable", headers=headers)
    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True

    health_response = api_client.post(f"/api/v1/admin/integrations/{integration_id}/health-check", headers=headers)
    assert health_response.status_code == 200

    test_response = api_client.post(
        f"/api/v1/admin/integrations/{integration_id}/test",
        json={"idempotency_key": "test-11-2:api"},
        headers=headers,
    )
    repeat_response = api_client.post(
        f"/api/v1/admin/integrations/{integration_id}/test",
        json={"idempotency_key": "test-11-2:api"},
        headers=headers,
    )
    assert test_response.status_code == 200
    assert repeat_response.status_code == 200
    assert repeat_response.json()["skipped"] is True

    executions_response = api_client.get(f"/api/v1/admin/integrations/{integration_id}/executions", headers=headers)
    assert executions_response.status_code == 200
    assert len(executions_response.json()) >= 2

    disable_response = api_client.post(f"/api/v1/admin/integrations/{integration_id}/disable", headers=headers)
    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False


def test_admin_api_authorization_and_protected_payloads(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    client_user = _create_user(db_session, UserRole.client)
    professional = _create_user(db_session, UserRole.professional)

    assert api_client.get("/api/v1/admin/integrations").status_code == 401
    assert api_client.get("/api/v1/admin/integrations", headers=_auth_headers(client_user)).status_code == 403
    assert api_client.get("/api/v1/admin/integrations", headers=_auth_headers(professional)).status_code == 403

    protected_payload = _integration_payload(name="Test 11.2 Protected")
    protected_payload["enabled"] = True
    response = api_client.post("/api/v1/admin/integrations", json=protected_payload, headers=_auth_headers(admin))
    assert response.status_code == 422


def test_admin_api_rejects_unsupported_provider_enable(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    headers = _auth_headers(admin)
    create_response = api_client.post(
        "/api/v1/admin/integrations",
        json=_integration_payload(name="Test 11.2 Future API", provider="google_meet", config={}),
        headers=headers,
    )
    assert create_response.status_code == 200
    integration_id = create_response.json()["id"]

    enable_response = api_client.post(f"/api/v1/admin/integrations/{integration_id}/enable", headers=headers)

    assert enable_response.status_code == 409


def test_admin_api_response_does_not_expose_secret_values(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    response = api_client.post(
        "/api/v1/admin/integrations",
        json=_integration_payload(name="Test 11.2 Safe Response"),
        headers=_auth_headers(admin),
    )

    assert response.status_code == 200
    assert "do-not-store" not in response.text
    assert "password" not in response.text.lower()
