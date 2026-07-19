from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db
from app.models.payment import MercadoPagoWebhookEvent, MercadoPagoWebhookProcessingStatus
from app.payments.providers.mercado_pago import mercado_pago_client_factory, parse_mercado_pago_config, resolve_secret_reference, verify_mercado_pago_signature
from app.payments.service import PaymentOrderService

router = APIRouter()


@router.post("/webhooks/mercado-pago")
async def mercado_pago_webhook(
    request: Request,
    data_id_query: str | None = Query(default=None, alias="data.id"),
    x_signature: str | None = Header(default=None, alias="x-signature"),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    payload = await request.json()
    data_id = data_id_query or _payload_data_id(payload)
    topic = _topic(payload)
    event_id = _event_id(payload, topic=topic, data_id=data_id, request_id=x_request_id)
    existing = db.query(MercadoPagoWebhookEvent).filter(MercadoPagoWebhookEvent.event_id == event_id).first()
    if existing:
        return {"status": "ok", "result": "duplicate"}

    event = MercadoPagoWebhookEvent(event_id=event_id, topic=topic, resource_id=data_id, signature_valid=False, processing_status=MercadoPagoWebhookProcessingStatus.received, received_at=datetime.now(UTC))
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "ok", "result": "duplicate"}

    try:
        integration = PaymentOrderService(db)._mercado_pago_integration(require_enabled=False)
        config = parse_mercado_pago_config(integration)
        secret = resolve_secret_reference(config["webhook_secret_reference"])
        if not verify_mercado_pago_signature(x_signature=x_signature, x_request_id=x_request_id, data_id=data_id, secret=secret):
            event.processing_status = MercadoPagoWebhookProcessingStatus.invalid_signature
            event.error_code = "mercado_pago_invalid_signature"
            event.error_message = "Firma Mercado Pago invalida."
            db.commit()
            return {"status": "ok", "result": "invalid_signature"}
        event.signature_valid = True
        if topic and "refund" in topic:
            event.processing_status = MercadoPagoWebhookProcessingStatus.ignored
            event.error_code = "mercado_pago_refund_sync_required"
            event.error_message = "Refund recibido; sincronizar desde administracion."
            event.processed_at = datetime.now(UTC)
            db.commit()
            return {"status": "ok", "result": "refund_sync_required"}
        if topic not in {"payment", "payment.created", "payment.updated"} or not data_id:
            event.processing_status = MercadoPagoWebhookProcessingStatus.ignored
            event.processed_at = datetime.now(UTC)
            db.commit()
            return {"status": "ok", "result": "ignored"}
        token = resolve_secret_reference(config["access_token_reference"])
        payment = mercado_pago_client_factory(token).get_payment(data_id)
        item = PaymentOrderService(db).apply_mercado_pago_payment(payment, None)
        event.payment_order_id = item.id if item else None
        event.processing_status = MercadoPagoWebhookProcessingStatus.processed if item else MercadoPagoWebhookProcessingStatus.ignored
        event.processed_at = datetime.now(UTC)
        db.commit()
        return {"status": "ok", "result": event.processing_status.value}
    except Exception as exc:
        event.processing_status = MercadoPagoWebhookProcessingStatus.failed
        event.error_code = "mercado_pago_webhook_failed"
        event.error_message = str(exc)[:300]
        event.processed_at = datetime.now(UTC)
        db.commit()
        return {"status": "ok", "result": "failed"}


def _payload_data_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if isinstance(data, dict) and data.get("id") is not None:
        return str(data["id"])
    if payload.get("resource") is not None:
        return str(payload["resource"]).rstrip("/").split("/")[-1]
    return str(payload["id"]) if payload.get("id") is not None else None


def _topic(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    return payload.get("type") or payload.get("topic") or payload.get("action")


def _event_id(payload: Any, *, topic: str | None, data_id: str | None, request_id: str | None) -> str:
    if isinstance(payload, dict) and payload.get("id") is not None:
        return str(payload["id"])
    return f"mercado_pago:{topic or 'unknown'}:{data_id or 'unknown'}:{request_id or 'no-request'}"
