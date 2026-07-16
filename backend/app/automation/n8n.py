from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.automation.contracts import DomainEvent
from app.automation.enums import WebhookDeliveryStatus, WebhookEventType
from app.automation.schemas import WebhookSubscriptionCreate, WebhookSubscriptionUpdate
from app.automation.service import WebhookDeliveryService, validate_target_url
from app.core.config import settings
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.models.integration import Integration
from app.models.n8n import N8nWorkflow
from app.models.user import User
from app.models.webhook import WebhookDelivery


N8N_ALLOWED_EVENTS = {
    WebhookEventType.appointment_created,
    WebhookEventType.appointment_cancelled,
    WebhookEventType.meeting_ready,
    WebhookEventType.document_generated,
    WebhookEventType.notification_failed,
}


def validate_n8n_config(config: dict) -> dict:
    base_url = str(config.get("base_url") or "").strip().rstrip("/")
    environment = str(config.get("environment") or "staging").strip()
    if not base_url:
        raise ValueError("n8n base_url is required")
    parsed = urlparse(base_url)
    if parsed.query or parsed.fragment:
        raise ValueError("n8n base_url cannot include query string or fragment")
    validate_target_url(base_url, app_env=settings.app_env)
    if not environment or len(environment) > 40:
        raise ValueError("n8n environment is invalid")
    return {"base_url": base_url, "environment": environment}


def validate_webhook_path(path: str) -> str:
    normalized = path.strip()
    if not normalized:
        raise ValueError("webhook_path is required")
    if "://" in normalized or normalized.startswith("//"):
        raise ValueError("webhook_path must be relative")
    if ".." in normalized.split("/"):
        raise ValueError("webhook_path cannot include traversal")
    if "?" in normalized or "#" in normalized:
        raise ValueError("webhook_path cannot include query string or fragment")
    if len(normalized) > 240:
        raise ValueError("webhook_path is too long")
    return normalized.lstrip("/")


def build_workflow_url(base_url: str, webhook_path: str) -> str:
    return urljoin(f"{base_url.rstrip('/')}/", validate_webhook_path(webhook_path))


class N8nWorkflowService:
    def __init__(self, db: Session, webhook_service: WebhookDeliveryService | None = None) -> None:
        self.db = db
        self.webhook_service = webhook_service or WebhookDeliveryService(db)

    def list_workflows(self, integration_id: int) -> list[N8nWorkflow]:
        self._require_integration(integration_id)
        return list(self.db.scalars(select(N8nWorkflow).where(N8nWorkflow.integration_id == integration_id).order_by(N8nWorkflow.created_at.desc(), N8nWorkflow.id.desc())))

    def get_workflow(self, integration_id: int, workflow_id: int) -> N8nWorkflow:
        workflow = self.db.get(N8nWorkflow, workflow_id)
        if not workflow or workflow.integration_id != integration_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="n8n workflow not found")
        return workflow

    def create_workflow(self, integration_id: int, payload, actor: User) -> N8nWorkflow:
        integration = self._require_integration(integration_id)
        event_types = self._event_values(payload.event_types)
        target_url = build_workflow_url(integration.config["base_url"], payload.webhook_path)
        subscription = self.webhook_service.create_subscription(
            WebhookSubscriptionCreate(
                integration_id=integration.id,
                name=f"n8n: {payload.name}",
                target_url=target_url,
                event_types=[WebhookEventType(event) for event in event_types],
                secret_reference=payload.secret_reference,
            ),
            actor,
        )
        workflow = N8nWorkflow(
            integration_id=integration.id,
            subscription_id=subscription.id,
            name=payload.name,
            description=payload.description,
            webhook_path=validate_webhook_path(payload.webhook_path),
            event_types=event_types,
            enabled=False,
            secret_reference=payload.secret_reference,
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def update_workflow(self, integration_id: int, workflow_id: int, payload, actor: User) -> N8nWorkflow:
        integration = self._require_integration(integration_id)
        workflow = self.get_workflow(integration_id, workflow_id)
        subscription_update: dict = {}
        if payload.name is not None:
            workflow.name = payload.name
            subscription_update["name"] = f"n8n: {payload.name}"
        if payload.description is not None:
            workflow.description = payload.description
        if payload.webhook_path is not None:
            workflow.webhook_path = validate_webhook_path(payload.webhook_path)
            subscription_update["target_url"] = build_workflow_url(integration.config["base_url"], workflow.webhook_path)
        if payload.event_types is not None:
            workflow.event_types = self._event_values(payload.event_types)
            subscription_update["event_types"] = [WebhookEventType(event) for event in workflow.event_types]
        if payload.secret_reference is not None:
            workflow.secret_reference = payload.secret_reference
            subscription_update["secret_reference"] = payload.secret_reference
        if subscription_update:
            self.webhook_service.update_subscription(workflow.subscription_id, WebhookSubscriptionUpdate(**subscription_update), actor)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def set_enabled(self, integration_id: int, workflow_id: int, enabled: bool, actor: User) -> N8nWorkflow:
        workflow = self.get_workflow(integration_id, workflow_id)
        self.webhook_service.set_enabled(workflow.subscription_id, enabled, actor)
        workflow.enabled = enabled
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def test_workflow(self, integration_id: int, workflow_id: int, actor: User) -> WebhookDelivery:
        workflow = self.get_workflow(integration_id, workflow_id)
        subscription = self.webhook_service.get_subscription(workflow.subscription_id)
        event = DomainEvent.create(
            event_type=WebhookEventType.n8n_workflow_test,
            entity_type="n8n_workflow",
            entity_id=workflow.id,
            payload={"message": "RealMeet n8n workflow test", "workflow_id": workflow.id},
        )
        delivery = self.webhook_service.deliver_to_subscription(subscription, event)
        self._sync_workflow_status(workflow, delivery)
        self.db.commit()
        return delivery

    def list_deliveries(self, integration_id: int, workflow_id: int, limit: int = 50) -> list[WebhookDelivery]:
        workflow = self.get_workflow(integration_id, workflow_id)
        return self.webhook_service.list_deliveries(subscription_id=workflow.subscription_id, limit=limit)

    def _sync_workflow_status(self, workflow: N8nWorkflow, delivery: WebhookDelivery) -> None:
        workflow.last_triggered_at = datetime.now(UTC)
        if delivery.status == WebhookDeliveryStatus.succeeded:
            workflow.last_success_at = datetime.now(UTC)
            workflow.last_error_code = None
        elif delivery.status == WebhookDeliveryStatus.failed:
            workflow.last_error_at = datetime.now(UTC)
            workflow.last_error_code = delivery.error_code

    def _require_integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
        if integration.provider != IntegrationProvider.n8n or integration.integration_type != IntegrationType.automation:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integration must be n8n automation")
        try:
            integration.config = validate_n8n_config(integration.config or {})
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        if integration.status == IntegrationStatus.unsupported:
            integration.status = IntegrationStatus.configured
        return integration

    @staticmethod
    def _event_values(events: list[WebhookEventType]) -> list[str]:
        if not events or len(set(events)) != len(events):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="event_types must be non-empty and unique")
        invalid = sorted({event for event in events if event not in N8N_ALLOWED_EVENTS})
        if invalid:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported n8n event type")
        return [event.value for event in events]
