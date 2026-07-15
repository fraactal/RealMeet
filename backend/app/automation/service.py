from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.automation.client import HttpOutboundWebhookClient, OutboundWebhookClient
from app.automation.contracts import DomainEvent
from app.automation.enums import WebhookDeliveryStatus, WebhookEventType
from app.automation.schemas import WebhookSubscriptionCreate, WebhookSubscriptionUpdate
from app.core.config import settings
from app.integrations.enums import IntegrationProvider
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.user import User
from app.models.webhook import WebhookDelivery, WebhookSubscription


LOCAL_ENVS = {"development", "docker", "test"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
ALLOWED_PROVIDERS = {IntegrationProvider.generic_webhook, IntegrationProvider.n8n}


class WebhookDeliveryService:
    def __init__(self, db: Session, client: OutboundWebhookClient | None = None) -> None:
        self.db = db
        self.client = client or HttpOutboundWebhookClient()

    def list_subscriptions(self) -> list[WebhookSubscription]:
        return list(self.db.scalars(select(WebhookSubscription).order_by(WebhookSubscription.created_at.desc(), WebhookSubscription.id.desc())))

    def get_subscription(self, subscription_id: int) -> WebhookSubscription:
        subscription = self.db.get(WebhookSubscription, subscription_id)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook subscription not found")
        return subscription

    def create_subscription(self, payload: WebhookSubscriptionCreate, actor: User) -> WebhookSubscription:
        integration = self._require_integration(payload.integration_id)
        self._validate_url(payload.target_url)
        subscription = WebhookSubscription(
            integration_id=integration.id,
            name=payload.name,
            target_url=payload.target_url,
            event_types=[event.value for event in payload.event_types],
            secret_reference=payload.secret_reference,
            enabled=False,
        )
        self.db.add(subscription)
        self.db.flush()
        self._audit(actor.id, "webhook_subscription_created", "WebhookSubscription", str(subscription.id), {"integration_id": integration.id})
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update_subscription(self, subscription_id: int, payload: WebhookSubscriptionUpdate, actor: User) -> WebhookSubscription:
        subscription = self.get_subscription(subscription_id)
        if payload.name is not None:
            subscription.name = payload.name
        if payload.target_url is not None:
            self._validate_url(payload.target_url)
            subscription.target_url = payload.target_url
        if payload.event_types is not None:
            subscription.event_types = [event.value for event in payload.event_types]
        if payload.secret_reference is not None:
            subscription.secret_reference = payload.secret_reference
        self._audit(actor.id, "webhook_subscription_updated", "WebhookSubscription", str(subscription.id), {"fields": sorted(payload.model_dump(exclude_none=True).keys())})
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def set_enabled(self, subscription_id: int, enabled: bool, actor: User) -> WebhookSubscription:
        subscription = self.get_subscription(subscription_id)
        if enabled:
            self._resolve_secret(subscription.secret_reference)
            self._validate_url(subscription.target_url)
        subscription.enabled = enabled
        self._audit(actor.id, "webhook_subscription_enabled" if enabled else "webhook_subscription_disabled", "WebhookSubscription", str(subscription.id), {})
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def list_deliveries(self, *, subscription_id: int | None = None, limit: int = 100) -> list[WebhookDelivery]:
        query = select(WebhookDelivery).order_by(WebhookDelivery.created_at.desc(), WebhookDelivery.id.desc()).limit(limit)
        if subscription_id is not None:
            query = query.where(WebhookDelivery.subscription_id == subscription_id)
        return list(self.db.scalars(query))

    def test_subscription(self, subscription_id: int, actor: User) -> WebhookDelivery:
        subscription = self.get_subscription(subscription_id)
        event = DomainEvent.create(
            event_type=WebhookEventType.webhook_test,
            entity_type="webhook_subscription",
            entity_id=subscription.id,
            payload={"message": "RealMeet webhook test"},
        )
        delivery = self.deliver_to_subscription(subscription, event)
        self._audit(actor.id, "webhook_subscription_tested", "WebhookDelivery", str(delivery.id), {"subscription_id": subscription.id, "status": delivery.status.value})
        return delivery

    def retry_delivery(self, delivery_id: int, actor: User) -> WebhookDelivery:
        delivery = self.db.get(WebhookDelivery, delivery_id)
        if not delivery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook delivery not found")
        if delivery.status != WebhookDeliveryStatus.failed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only failed webhook deliveries can be retried")
        subscription = self.get_subscription(delivery.subscription_id)
        event = DomainEvent(
            event_id=delivery.event_id,
            event_type=WebhookEventType(delivery.event_type),
            event_version=1,
            occurred_at=datetime.now(UTC),
            entity_type=delivery.event_type.split(".")[0],
            entity_id=delivery.event_id.rsplit(":", 2)[-2] if ":" in delivery.event_id else delivery.event_id,
            correlation_id=delivery.event_id,
            payload={"retry": True, "original_event_id": delivery.event_id},
        )
        retried = self._send(subscription, event, delivery=delivery)
        self._audit(actor.id, "webhook_delivery_retried", "WebhookDelivery", str(delivery.id), {"subscription_id": subscription.id, "status": retried.status.value})
        return retried

    def publish(self, event: DomainEvent) -> list[WebhookDelivery]:
        subscriptions = list(
            self.db.scalars(
                select(WebhookSubscription).where(
                    WebhookSubscription.enabled.is_(True),
                )
            )
        )
        deliveries: list[WebhookDelivery] = []
        for subscription in subscriptions:
            if event.event_type.value not in subscription.event_types:
                continue
            try:
                deliveries.append(self.deliver_to_subscription(subscription, event))
            except Exception:
                self.db.rollback()
        return deliveries

    def deliver_to_subscription(self, subscription: WebhookSubscription, event: DomainEvent) -> WebhookDelivery:
        if not subscription.enabled:
            delivery = self._ensure_delivery(subscription, event)
            delivery.status = WebhookDeliveryStatus.skipped
            delivery.error_code = "subscription_disabled"
            delivery.error_message = "La suscripcion esta deshabilitada."
            self.db.commit()
            return delivery
        return self._send(subscription, event)

    def _send(self, subscription: WebhookSubscription, event: DomainEvent, *, delivery: WebhookDelivery | None = None) -> WebhookDelivery:
        delivery = delivery or self._ensure_delivery(subscription, event)
        if delivery.status == WebhookDeliveryStatus.succeeded:
            return delivery
        secret = self._resolve_secret(subscription.secret_reference)
        payload = event.as_payload()
        timestamp = datetime.now(UTC).isoformat()
        signature = sign_payload(payload, secret=secret, timestamp=timestamp)
        headers = {
            "X-RealMeet-Signature": signature,
            "X-RealMeet-Event": event.event_type.value,
            "X-RealMeet-Delivery": str(delivery.id),
            "X-RealMeet-Timestamp": timestamp,
        }
        self._validate_url(subscription.target_url)
        delivery.status = WebhookDeliveryStatus.sending
        delivery.attempt += 1 if delivery.attempt > 0 and delivery.error_code else 0
        self.db.commit()
        result = self.client.send(target_url=subscription.target_url, headers=headers, json_payload=payload)
        delivery.response_status = result.status_code
        delivery.duration_ms = result.duration_ms
        delivery.status = WebhookDeliveryStatus.succeeded if result.success else WebhookDeliveryStatus.failed
        delivery.error_code = None if result.success else result.error_code
        delivery.error_message = None if result.success else result.error_message
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def _ensure_delivery(self, subscription: WebhookSubscription, event: DomainEvent) -> WebhookDelivery:
        existing = self.db.scalar(select(WebhookDelivery).where(WebhookDelivery.subscription_id == subscription.id, WebhookDelivery.event_id == event.event_id))
        if existing:
            return existing
        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event_id=event.event_id,
            event_type=event.event_type.value,
            status=WebhookDeliveryStatus.pending,
            attempt=1,
            idempotency_key=f"{subscription.id}:{event.event_id}",
        )
        self.db.add(delivery)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return self.db.scalar(select(WebhookDelivery).where(WebhookDelivery.subscription_id == subscription.id, WebhookDelivery.event_id == event.event_id))
        self.db.refresh(delivery)
        return delivery

    def _require_integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
        if integration.provider not in ALLOWED_PROVIDERS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integration provider must be generic_webhook or n8n")
        return integration

    def _resolve_secret(self, reference: str) -> str:
        value = os.environ.get(reference)
        if not value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook secret reference is not configured")
        return value

    def _validate_url(self, value: str) -> None:
        validate_target_url(value, app_env=settings.app_env)

    def _audit(self, user_id: int | None, action: str, entity_name: str, entity_id: str, metadata: dict) -> None:
        self.db.add(AuditLog(user_id=user_id, action=action, entity_name=entity_name, entity_id=entity_id, metadata_json=metadata, created_at=datetime.now(UTC)))


class DomainEventPublisher:
    def __init__(self, db: Session, delivery_service: WebhookDeliveryService | None = None) -> None:
        self.db = db
        self.delivery_service = delivery_service or WebhookDeliveryService(db)

    def publish_appointment_created(self, appointment: Appointment) -> list[WebhookDelivery]:
        return self.delivery_service.publish(self._appointment_event(WebhookEventType.appointment_created, appointment))

    def publish_appointment_cancelled(self, appointment: Appointment) -> list[WebhookDelivery]:
        return self.delivery_service.publish(self._appointment_event(WebhookEventType.appointment_cancelled, appointment))

    def _appointment_event(self, event_type: WebhookEventType, appointment: Appointment) -> DomainEvent:
        return DomainEvent.create(
            event_type=event_type,
            entity_type="appointment",
            entity_id=appointment.id,
            correlation_id=f"appointment:{appointment.id}",
            payload={
                "appointment_id": appointment.id,
                "status": appointment.status.value,
                "starts_at": appointment.start_datetime.isoformat(),
                "professional_id": appointment.professional_id,
                "client_id": appointment.client_id,
                "modality": appointment.consultation_mode.value,
            },
        )


def sign_payload(payload: dict, *, secret: str, timestamp: str) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}.{body}".encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def validate_target_url(value: str, *, app_env: str) -> None:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Webhook URL must be absolute")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Webhook URL cannot include credentials")
    host = parsed.hostname
    if not host:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Webhook URL host is required")
    local_env = app_env in LOCAL_ENVS
    if parsed.scheme != "https":
        if not (local_env and parsed.scheme == "http" and host in LOCAL_HOSTS):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Webhook URL must use HTTPS")
    if host in LOCAL_HOSTS and not local_env:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Webhook URL host is not allowed")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if (ip.is_private or ip.is_loopback or ip.is_link_local) and not local_env:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Webhook URL IP is not allowed")
