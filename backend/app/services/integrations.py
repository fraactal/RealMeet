from datetime import UTC, datetime
import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import (
    IntegrationConfigurationError,
    IntegrationDisabledError,
    IntegrationError,
    IntegrationExecutionInProgressError,
    IntegrationNotFoundError,
    IntegrationOperationUnsupportedError,
    IntegrationProviderExecutionError,
    IntegrationProviderUnexpectedError,
)
from app.integrations.registry import IntegrationProviderRegistry, provider_registry
from app.integrations.results import IntegrationResult
from app.models.audit_log import AuditLog
from app.models.integration import Integration, IntegrationExecution
from app.models.user import User
from app.repositories.integration_execution_repository import IntegrationExecutionRepository
from app.repositories.integration_repository import IntegrationRepository
from app.schemas.integrations import IntegrationCreate, IntegrationExecutionCreate, IntegrationUpdate
from app.services.google_meet import GoogleMeetService
from app.whatsapp.configuration import validate_whatsapp_local_configuration
from app.payments.providers.mercado_pago import parse_mercado_pago_config

logger = logging.getLogger("realmeet.integrations")


class IntegrationService:
    def __init__(self, db: Session, registry: IntegrationProviderRegistry = provider_registry) -> None:
        self.db = db
        self.registry = registry
        self.integrations = IntegrationRepository(db)
        self.executions = IntegrationExecutionRepository(db)

    def list_integrations(
        self,
        *,
        integration_type: IntegrationType | None = None,
        provider: IntegrationProvider | None = None,
        enabled: bool | None = None,
        status: IntegrationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Integration], int]:
        total = self.integrations.count_filtered(integration_type=integration_type, provider=provider, enabled=enabled, status=status)
        items = list(
            self.integrations.list_filtered(
                integration_type=integration_type,
                provider=provider,
                enabled=enabled,
                status=status,
                offset=(page - 1) * page_size,
                limit=page_size,
            )
        )
        return items, total

    def get_integration(self, integration_id: int) -> Integration:
        integration = self.integrations.get(integration_id)
        if not integration:
            raise IntegrationNotFoundError("Integracion no encontrada", code="integration_not_found")
        return integration

    def create_integration(self, payload: IntegrationCreate, admin_user: User) -> Integration:
        integration = self.integrations.create(payload)
        integration.enabled = False
        if integration.provider == IntegrationProvider.mercado_pago:
            parse_mercado_pago_config(integration)
        if integration.provider in {IntegrationProvider.whatsapp_cloud, IntegrationProvider.n8n, IntegrationProvider.generic_webhook}:
            integration.status = IntegrationStatus.configured
        else:
            integration.status = IntegrationStatus.configured if self.registry.is_supported(integration.provider) else IntegrationStatus.unsupported
        self._audit(admin_user, "integration_created", integration, {"result": "created"})
        self._commit()
        self.db.refresh(integration)
        return integration

    def update_integration(self, integration_id: int, payload: IntegrationUpdate, admin_user: User) -> Integration:
        integration = self.get_integration(integration_id)
        changes = payload.model_dump(exclude_unset=True)
        self.integrations.update_allowed_fields(integration, payload)
        if integration.provider == IntegrationProvider.mercado_pago and {"config", "secret_reference"} & set(changes):
            parse_mercado_pago_config(integration)
        if {"config", "secret_reference"} & set(changes):
            integration.status = IntegrationStatus.configured if integration.provider in {IntegrationProvider.whatsapp_cloud, IntegrationProvider.n8n, IntegrationProvider.generic_webhook} or self.registry.is_supported(integration.provider) else IntegrationStatus.unsupported
            integration.last_error_message = None
        self._audit(admin_user, "integration_updated", integration, {"fields": sorted(changes.keys()), "result": "updated"})
        self._commit()
        self.db.refresh(integration)
        return integration

    def validate_configuration(self, integration_id: int, admin_user: User) -> IntegrationResult:
        integration = self.get_integration(integration_id)
        provider = self.registry.get(integration.provider)
        try:
            result = provider.validate_configuration(integration)
        except IntegrationConfigurationError as exc:
            integration.status = IntegrationStatus.error
            integration.last_error_at = datetime.now(UTC)
            integration.last_error_message = exc.message
            self._audit(admin_user, "integration_validated", integration, {"result": "failed", "code": exc.code})
            self._commit()
            raise
        integration.status = IntegrationStatus.configured
        integration.last_error_message = None
        self._audit(admin_user, "integration_validated", integration, {"result": "succeeded", "code": result.code})
        self._commit()
        return result

    def enable_integration(self, integration_id: int, admin_user: User) -> Integration:
        integration = self.get_integration(integration_id)
        if integration.provider == IntegrationProvider.google_meet:
            GoogleMeetService(self.db).validate_enable_ready(integration)
            integration.enabled = True
            integration.status = IntegrationStatus.configured
            self._audit(admin_user, "integration_enabled", integration, {"result": "enabled", "scope": "admin_google_meet"})
            self._commit()
            self.db.refresh(integration)
            return integration
        if integration.provider == IntegrationProvider.whatsapp_cloud:
            validate_whatsapp_local_configuration(integration)
            integration.enabled = True
            integration.status = IntegrationStatus.configured
            self._audit(admin_user, "integration_enabled", integration, {"result": "enabled", "scope": "admin_whatsapp_cloud"})
            self._commit()
            self.db.refresh(integration)
            return integration
        self.validate_configuration(integration.id, admin_user)
        integration.enabled = True
        if integration.status == IntegrationStatus.not_configured:
            integration.status = IntegrationStatus.configured
        self._audit(admin_user, "integration_enabled", integration, {"result": "enabled"})
        self._commit()
        self.db.refresh(integration)
        return integration

    def disable_integration(self, integration_id: int, admin_user: User) -> Integration:
        integration = self.get_integration(integration_id)
        integration.enabled = False
        self._audit(admin_user, "integration_disabled", integration, {"result": "disabled"})
        self._commit()
        self.db.refresh(integration)
        return integration

    def health_check(self, integration_id: int, admin_user: User, *, idempotency_key: str | None = None) -> IntegrationResult:
        integration = self.get_integration(integration_id)
        if integration.provider == IntegrationProvider.google_meet:
            result = GoogleMeetService(self.db).health_check(integration, admin_user)
            return IntegrationResult.ok(
                code="google_meet_health_ok",
                message="Health check Google Meet exitoso",
                metadata={"provider": "google_meet", "calendar_id": result.external_calendar_id},
            )
        self._ensure_enabled(integration)
        key = idempotency_key or f"integration:{integration.id}:health:{datetime.now(UTC).isoformat()}"
        result = self._execute_with_idempotency(integration, operation="health_check", idempotency_key=key, provider_operation="health_check")
        integration.last_checked_at = datetime.now(UTC)
        if result.success:
            integration.status = IntegrationStatus.healthy
            integration.last_success_at = result.finished_at
            integration.last_error_message = None
        else:
            integration.status = IntegrationStatus.error
            integration.last_error_at = result.finished_at
            integration.last_error_message = result.message
        self._audit(admin_user, "integration_health_checked", integration, {"result": "succeeded" if result.success else "failed", "code": result.code})
        self._commit()
        return result

    def test_integration(self, integration_id: int, admin_user: User, *, idempotency_key: str) -> IntegrationResult:
        integration = self.get_integration(integration_id)
        self._ensure_enabled(integration)
        if integration.provider != IntegrationProvider.mock:
            raise IntegrationConfigurationError("La prueba manual solo esta disponible para el proveedor mock", code="mock_test_only")
        result = self._execute_with_idempotency(integration, operation="test", idempotency_key=idempotency_key, provider_operation="test")
        self._audit(admin_user, "integration_tested", integration, {"result": "skipped" if result.skipped else "succeeded" if result.success else "failed", "code": result.code})
        self._commit()
        return result

    def list_executions(self, integration_id: int, *, limit: int = 20) -> list[IntegrationExecution]:
        self.get_integration(integration_id)
        return list(self.executions.list_recent_for_integration(integration_id, limit=limit))

    def _execute_with_idempotency(self, integration: Integration, *, operation: str, idempotency_key: str, provider_operation: str) -> IntegrationResult:
        existing = self.executions.get_by_idempotency_key(integration.id, idempotency_key)
        if existing:
            if existing.status == IntegrationExecutionStatus.succeeded:
                return IntegrationResult.skipped_idempotent(
                    message="Operacion ya procesada",
                    metadata={"integration_id": integration.id, "execution_id": existing.id, "operation": operation},
                )
            if existing.status in {IntegrationExecutionStatus.pending, IntegrationExecutionStatus.running}:
                raise IntegrationExecutionInProgressError("La ejecucion ya esta en proceso", code="execution_in_progress")
            execution = existing
            execution.attempt += 1
            execution.status = IntegrationExecutionStatus.running
            execution.started_at = datetime.now(UTC)
            execution.finished_at = None
            execution.error_code = None
            execution.error_message = None
            execution.response_metadata = None
        else:
            try:
                execution = self.executions.create(
                    IntegrationExecutionCreate(
                        integration_id=integration.id,
                        operation=operation,
                        idempotency_key=idempotency_key,
                        status=IntegrationExecutionStatus.running,
                        started_at=datetime.now(UTC),
                        request_metadata={"operation": operation, "provider": integration.provider.value},
                    )
                )
            except IntegrityError as exc:
                self.db.rollback()
                raise IntegrationExecutionInProgressError("La ejecucion ya existe", code="execution_conflict") from exc

        self.db.flush()
        provider = self.registry.get(integration.provider)
        try:
            if provider_operation == "health_check":
                result = provider.health_check(integration)
            else:
                result = provider.execute(integration, provider_operation, payload={"operation": operation})
            execution.status = IntegrationExecutionStatus.succeeded
            execution.response_metadata = self._result_metadata(result)
            execution.error_code = None
            execution.error_message = None
        except IntegrationProviderExecutionError as exc:
            result = IntegrationResult.failed(code=exc.code, message=exc.message, metadata={"provider": integration.provider.value, "operation": operation})
            execution.status = IntegrationExecutionStatus.failed
            execution.response_metadata = self._result_metadata(result)
            execution.error_code = exc.code
            execution.error_message = exc.message
        except IntegrationError:
            raise
        except Exception as exc:
            raise IntegrationProviderUnexpectedError("Error inesperado del proveedor", code="provider_unexpected_error") from exc
        finally:
            execution.finished_at = datetime.now(UTC)
            self.db.flush()

        logger.info(
            "integration_execution integration_id=%s provider=%s operation=%s execution_id=%s attempt=%s status=%s duration_ms=%s code=%s",
            integration.id,
            integration.provider.value,
            operation,
            execution.id,
            execution.attempt,
            execution.status.value,
            result.duration_ms,
            result.code,
        )
        result.execution_id = execution.id  # type: ignore[attr-defined]
        return result

    @staticmethod
    def _result_metadata(result: IntegrationResult) -> dict[str, Any]:
        return {"code": result.code, "metadata": result.metadata, "duration_ms": result.duration_ms}

    @staticmethod
    def _ensure_enabled(integration: Integration) -> None:
        if not integration.enabled:
            raise IntegrationDisabledError("La integracion esta deshabilitada", code="integration_disabled")

    def _audit(self, admin_user: User, action: str, integration: Integration, metadata: dict[str, Any]) -> None:
        safe_metadata = {
            "integration_id": integration.id,
            "provider": integration.provider.value,
            "integration_type": integration.integration_type.value,
            **metadata,
        }
        self.db.add(
            AuditLog(
                user_id=admin_user.id,
                action=action,
                entity_name="Integration",
                entity_id=str(integration.id),
                metadata_json=safe_metadata,
                created_at=datetime.now(UTC),
            )
        )

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
