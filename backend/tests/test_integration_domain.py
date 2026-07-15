from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType
from app.models.integration import Integration, IntegrationExecution
from app.repositories.integration_execution_repository import IntegrationExecutionRepository
from app.repositories.integration_repository import IntegrationRepository
from app.schemas.integrations import IntegrationCreate, IntegrationExecutionCreate, IntegrationUpdate


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.execute(delete(IntegrationExecution).where(IntegrationExecution.idempotency_key.like("test-11-1:%")))
        db.execute(delete(Integration).where(Integration.name.like("Test 11.1%")))
        db.commit()
        db.close()


def _integration_payload(**overrides) -> dict:
    payload = {
        "name": "Test 11.1 Mock",
        "integration_type": IntegrationType.automation,
        "provider": IntegrationProvider.mock,
        "config": {"mode": "noop", "options": {"timeout": 5}},
        "secret_reference": "MOCK_INTEGRATION_SECRET",
    }
    payload.update(overrides)
    return payload


def _create_integration(db_session, name: str = "Test 11.1 Mock") -> Integration:
    integration = IntegrationRepository(db_session).create(IntegrationCreate(**_integration_payload(name=name)))
    db_session.commit()
    db_session.refresh(integration)
    return integration


def test_integration_create_schema_accepts_valid_payload() -> None:
    payload = IntegrationCreate(**_integration_payload())

    assert payload.integration_type == IntegrationType.automation
    assert payload.provider == IntegrationProvider.mock
    assert payload.secret_reference == "MOCK_INTEGRATION_SECRET"


def test_integration_config_rejects_sensitive_top_level_key() -> None:
    with pytest.raises(ValidationError):
        IntegrationCreate(**_integration_payload(config={"access_token": "do-not-store"}))


def test_integration_config_rejects_sensitive_nested_key() -> None:
    with pytest.raises(ValidationError):
        IntegrationCreate(**_integration_payload(config={"oauth": {"client-secret": "do-not-store"}}))


def test_integration_config_rejects_sensitive_key_inside_list() -> None:
    with pytest.raises(ValidationError):
        IntegrationCreate(**_integration_payload(config={"items": [{"private_key": "do-not-store"}]}))


def test_secret_reference_accepts_environment_variable_format() -> None:
    payload = IntegrationCreate(**_integration_payload(secret_reference="GOOGLE_MEET_CLIENT_SECRET"))

    assert payload.secret_reference == "GOOGLE_MEET_CLIENT_SECRET"


@pytest.mark.parametrize("secret_reference", ["abc123", "mi-clave-secreta", "Bearer eyJhbGciOi", "https://example.test/secret"])
def test_secret_reference_rejects_values_that_do_not_look_like_references(secret_reference: str) -> None:
    with pytest.raises(ValidationError):
        IntegrationCreate(**_integration_payload(secret_reference=secret_reference))


def test_integration_schemas_reject_protected_fields_and_mass_assignment() -> None:
    with pytest.raises(ValidationError):
        IntegrationCreate(**_integration_payload(enabled=True))

    with pytest.raises(ValidationError):
        IntegrationUpdate(provider=IntegrationProvider.twilio)


def test_repository_persists_integration_disabled_by_default(db_session) -> None:
    integration = _create_integration(db_session)

    assert integration.id is not None
    assert integration.enabled is False
    assert integration.status == IntegrationStatus.not_configured
    assert integration.config == {"mode": "noop", "options": {"timeout": 5}}


def test_repository_persists_integration_execution(db_session) -> None:
    integration = _create_integration(db_session, name="Test 11.1 Execution")
    execution = IntegrationExecutionRepository(db_session).create(
        IntegrationExecutionCreate(
            integration_id=integration.id,
            operation="health_check",
            entity_type="integration",
            entity_id=str(integration.id),
            idempotency_key="test-11-1:execution:create",
            status=IntegrationExecutionStatus.succeeded,
            request_metadata={"source": "test"},
            response_metadata={"ok": True},
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
    )
    db_session.commit()
    db_session.refresh(execution)

    assert execution.id is not None
    assert execution.attempt == 1
    assert execution.status == IntegrationExecutionStatus.succeeded


def test_unique_idempotency_key_per_integration_is_enforced(db_session) -> None:
    integration = _create_integration(db_session, name="Test 11.1 Unique")
    repository = IntegrationExecutionRepository(db_session)
    payload = IntegrationExecutionCreate(
        integration_id=integration.id,
        operation="test",
        idempotency_key="test-11-1:unique",
    )
    repository.create(payload)
    db_session.commit()

    with pytest.raises(IntegrityError):
        repository.create(payload)
        db_session.commit()


def test_execution_can_be_found_by_idempotency_key(db_session) -> None:
    integration = _create_integration(db_session, name="Test 11.1 Idempotency")
    repository = IntegrationExecutionRepository(db_session)
    repository.create(
        IntegrationExecutionCreate(
            integration_id=integration.id,
            operation="test",
            idempotency_key="test-11-1:lookup",
        )
    )
    db_session.commit()

    found = repository.get_by_idempotency_key(integration.id, "test-11-1:lookup")

    assert found is not None
    assert found.operation == "test"


def test_execution_metadata_rejects_sensitive_keys() -> None:
    with pytest.raises(ValidationError):
        IntegrationExecutionCreate(
            integration_id=1,
            operation="test",
            idempotency_key="test-11-1:sensitive-metadata",
            request_metadata={"headers": {"Authorization": "Bearer token"}},
        )
