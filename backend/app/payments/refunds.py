from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationProvider, IntegrationType
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import Integration
from app.models.payment import PaymentOrder, PaymentRefund, PaymentRefundReasonCode, PaymentRefundStatus, PaymentRefundStatusHistory
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User, UserRole
from app.payments.contracts import PaymentProviderError, PaymentRefundInput, PaymentRefundProviderResult
from app.payments.enums import PaymentCurrency, PaymentOrderStatus, PaymentProviderKey
from app.payments.providers.mercado_pago import mercado_pago_client_factory, parse_mercado_pago_config, resolve_secret_reference
from app.payments.registry import payment_provider_registry
from app.payments.schemas import PaymentRefundCreate

APPROVED_REFUND_STATUSES = {PaymentRefundStatus.approved}
FINAL_REFUND_STATUSES = {PaymentRefundStatus.approved, PaymentRefundStatus.rejected, PaymentRefundStatus.cancelled, PaymentRefundStatus.failed}


class PaymentRefundService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_admin(self, payment_order_id: int) -> list[PaymentRefund]:
        self._order(payment_order_id)
        return list(self.db.scalars(select(PaymentRefund).where(PaymentRefund.payment_order_id == payment_order_id).order_by(PaymentRefund.created_at.desc(), PaymentRefund.id.desc())))

    def list_for_professional(self, payment_order_id: int, user: User) -> list[PaymentRefund]:
        order = self._order(payment_order_id)
        professional = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        if user.role != UserRole.professional or not professional or order.professional_id != professional.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        return self.list_admin(payment_order_id)

    def list_for_client(self, payment_order_id: int, user: User) -> list[PaymentRefund]:
        order = self._order(payment_order_id)
        client = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if user.role != UserRole.client or not client or order.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        return self.list_admin(payment_order_id)

    def get(self, refund_id: int) -> PaymentRefund:
        item = self.db.get(PaymentRefund, refund_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment refund not found")
        return item

    def list_history(self, refund_id: int) -> list[PaymentRefundStatusHistory]:
        self.get(refund_id)
        return list(self.db.scalars(select(PaymentRefundStatusHistory).where(PaymentRefundStatusHistory.refund_id == refund_id).order_by(PaymentRefundStatusHistory.created_at.asc(), PaymentRefundStatusHistory.id.asc())))

    def create(self, payment_order_id: int, payload: PaymentRefundCreate, actor: User, idempotency_key: str | None = None) -> PaymentRefund:
        order = self._order(payment_order_id, lock=True)
        if order.status != PaymentOrderStatus.approved:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_refund_order_not_approved"})
        if payload.currency != order.currency:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_refund_currency_mismatch"})
        if payload.reason_code == PaymentRefundReasonCode.other and not (payload.reason_summary or "").strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_refund_reason_summary_required"})
        self._validate_amount(payload.amount, payload.currency)
        refundable = self.refundable_amount(order)
        if payload.amount > refundable:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_refund_amount_exceeds_refundable"})
        fingerprint = self._fingerprint({"payment_order_id": payment_order_id, "amount": payload.amount, "currency": payload.currency, "reason_code": payload.reason_code, "reason_summary": payload.reason_summary})
        key = idempotency_key or f"payment-refund:order:{payment_order_id}:{fingerprint[:32]}"
        existing = self.db.scalar(select(PaymentRefund).where(PaymentRefund.idempotency_key == key))
        if existing:
            if existing.request_fingerprint != fingerprint:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_refund_idempotency_conflict"})
            return existing
        item = PaymentRefund(payment_order_id=order.id, provider=order.provider, idempotency_key=key, request_fingerprint=fingerprint, amount=payload.amount, currency=payload.currency, reason_code=payload.reason_code, reason_summary=payload.reason_summary, requested_by_user_id=actor.id, requested_at=datetime.now(UTC))
        self.db.add(item)
        try:
            self.db.flush()
            self._add_history(item, None, item.status, "payment_refund_requested", "Reembolso solicitado.", actor, None)
            self._publish_refund_event("payment.refund.requested", item)
            self._refresh_order_refund_summary(order)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_refund_idempotency_conflict"}) from exc
        self.db.refresh(item)
        return item

    async def submit(self, refund_id: int, actor: User) -> PaymentRefund:
        return self._submit_sync(self.get(refund_id), actor)

    def _submit_sync(self, refund: PaymentRefund, actor: User) -> PaymentRefund:
        if refund.status == PaymentRefundStatus.approved:
            return refund
        if refund.status not in {PaymentRefundStatus.requested, PaymentRefundStatus.failed, PaymentRefundStatus.reconcile_required}:
            return refund
        order = self._order(refund.payment_order_id, lock=True)
        if refund.external_refund_id:
            return self.sync_provider(refund.id, actor)
        self._transition(refund, PaymentRefundStatus.processing, "payment_refund_processing", "Reembolso enviado al provider.", actor, None)
        key = f"{refund.idempotency_key or f'payment-refund:{refund.id}'}:provider:create-refund"
        try:
            result = self._create_provider_refund(order, refund, key)
        except PaymentProviderError as exc:
            refund.last_error_code = self._sanitize(exc.code)[:120]
            refund.last_error_message = self._sanitize(exc.message)
            refund.failed_at = datetime.now(UTC)
            self._transition(refund, PaymentRefundStatus.failed, refund.last_error_code, refund.last_error_message, actor, {"provider": refund.provider.value})
            self._refresh_order_refund_summary(order)
            self._publish_refund_event("payment.refund.failed", refund)
            self.db.commit()
            self.db.refresh(refund)
            return refund
        self._apply_provider_result(refund, result, actor)
        self._refresh_order_refund_summary(order)
        self.db.commit()
        self.db.refresh(refund)
        return refund

    def fake_approve(self, refund_id: int, actor: User) -> PaymentRefund:
        refund = self.get(refund_id)
        if refund.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_refund_provider_not_fake"})
        result = PaymentRefundProviderResult(external_refund_id=refund.external_refund_id or f"fake_ref_manual_{refund.id}", status="approved", amount=refund.amount, currency=refund.currency, processed_at=datetime.now(UTC), provider_reference={"provider": "fake", "operation": "approve_refund"})
        self._apply_provider_result(refund, result, actor)
        self._refresh_order_refund_summary(refund.payment_order)
        self.db.commit()
        self.db.refresh(refund)
        return refund

    def fake_reject(self, refund_id: int, actor: User) -> PaymentRefund:
        refund = self.get(refund_id)
        if refund.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_refund_provider_not_fake"})
        result = PaymentRefundProviderResult(external_refund_id=refund.external_refund_id or f"fake_ref_reject_{refund.id}", status="rejected", amount=refund.amount, currency=refund.currency, provider_reference={"provider": "fake", "operation": "reject_refund"})
        self._apply_provider_result(refund, result, actor)
        self._refresh_order_refund_summary(refund.payment_order)
        self.db.commit()
        self.db.refresh(refund)
        return refund

    def fake_fail(self, refund_id: int, actor: User) -> PaymentRefund:
        refund = self.get(refund_id)
        if refund.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_refund_provider_not_fake"})
        refund.last_error_code = "fake_refund_failed"
        refund.last_error_message = "Fallo fake controlado."
        refund.failed_at = datetime.now(UTC)
        self._transition(refund, PaymentRefundStatus.failed, refund.last_error_code, refund.last_error_message, actor, {"provider": "fake", "operation": "fail_refund"})
        self._refresh_order_refund_summary(refund.payment_order)
        self._publish_refund_event("payment.refund.failed", refund)
        self.db.commit()
        self.db.refresh(refund)
        return refund

    def sync_provider(self, refund_id: int, actor: User) -> PaymentRefund:
        refund = self.get(refund_id)
        order = refund.payment_order
        if not refund.external_refund_id:
            refund.last_error_code = "provider_refund_not_found"
            refund.last_error_message = "Refund externo no disponible."
            refund.status = PaymentRefundStatus.reconcile_required
            self._add_history(refund, None, refund.status, "provider_refund_not_found", refund.last_error_message, actor, None)
            self.db.commit()
            self.db.refresh(refund)
            return refund
        try:
            result = self._get_provider_refund(order, refund)
        except PaymentProviderError as exc:
            refund.last_error_code = self._sanitize(exc.code)[:120]
            refund.last_error_message = self._sanitize(exc.message)
            refund.status = PaymentRefundStatus.reconcile_required
            self.db.commit()
            self.db.refresh(refund)
            return refund
        self._apply_provider_result(refund, result, actor)
        self._refresh_order_refund_summary(order)
        self.db.commit()
        self.db.refresh(refund)
        return refund

    def retry(self, refund_id: int, actor: User) -> PaymentRefund:
        refund = self.get(refund_id)
        if refund.status not in {PaymentRefundStatus.failed, PaymentRefundStatus.reconcile_required}:
            return refund
        if refund.external_refund_id:
            return self.sync_provider(refund.id, actor)
        return self._submit_sync(refund, actor)

    def reconcile(self, refund_id: int, actor: User) -> tuple[str, PaymentRefund]:
        refund = self.get(refund_id)
        order = refund.payment_order
        if refund.external_refund_id and refund.status in {PaymentRefundStatus.processing, PaymentRefundStatus.reconcile_required}:
            self.sync_provider(refund.id, actor)
            self.db.refresh(refund)
            return "provider_sync_required", refund
        approved_sum = self._approved_sum(order.id)
        if approved_sum > order.amount:
            return "refund_amount_mismatch", refund
        expected_status = self._summary_status(order, approved_sum)
        if order.refunded_amount != approved_sum or order.refund_status != expected_status or (approved_sum == order.amount and order.status != PaymentOrderStatus.refunded):
            self._refresh_order_refund_summary(order)
            self.db.commit()
            self.db.refresh(refund)
            return "payment_order_status_mismatch", refund
        return "in_sync", refund

    def refundable_amount(self, order: PaymentOrder) -> Decimal:
        return order.amount - self._approved_sum(order.id)

    def _create_provider_refund(self, order: PaymentOrder, refund: PaymentRefund, key: str):
        if order.provider == PaymentProviderKey.fake:
            reason = (refund.reason_summary or refund.reason_code.value).lower()
            if "fail" in reason:
                raise PaymentProviderError("Fallo fake controlado.", code="fake_refund_failed")
            provider_status = "rejected" if "reject" in reason else "processing" if "pending" in reason else "approved"
            return PaymentRefundProviderResult(external_refund_id=refund.external_refund_id or f"fake_ref_{refund.id}", status=provider_status, amount=refund.amount, currency=refund.currency, processed_at=datetime.now(UTC) if provider_status == "approved" else None, provider_reference={"provider": "fake", "operation": "create_refund", "status": provider_status})
        if order.provider == PaymentProviderKey.mercado_pago:
            if not order.external_payment_id:
                raise PaymentProviderError("Payment externo no disponible.", code="provider_payment_not_found")
            integration = self._mercado_pago_integration()
            config = parse_mercado_pago_config(integration)
            token = resolve_secret_reference(config["access_token_reference"])
            return mercado_pago_client_factory(token).create_refund(order.external_payment_id, amount=refund.amount, currency=refund.currency, idempotency_key=key)
        raise PaymentProviderError("Provider no soporta reembolsos.", code="payment_refund_provider_not_supported")

    def _get_provider_refund(self, order: PaymentOrder, refund: PaymentRefund):
        if order.provider == PaymentProviderKey.fake:
            return PaymentRefundProviderResult(external_refund_id=refund.external_refund_id or f"fake_ref_manual_{refund.id}", status="approved", amount=refund.amount, currency=refund.currency, processed_at=datetime.now(UTC), provider_reference={"provider": "fake", "operation": "get_refund"})
        if order.provider == PaymentProviderKey.mercado_pago:
            if not order.external_payment_id:
                raise PaymentProviderError("Payment externo no disponible.", code="provider_payment_not_found")
            integration = self._mercado_pago_integration(require_enabled=False)
            config = parse_mercado_pago_config(integration)
            token = resolve_secret_reference(config["access_token_reference"])
            return mercado_pago_client_factory(token).get_refund(order.external_payment_id, refund.external_refund_id, currency=refund.currency)
        raise PaymentProviderError("Provider no soporta reembolsos.", code="payment_refund_provider_not_supported")

    def _apply_provider_result(self, refund: PaymentRefund, result, actor: User | None) -> None:
        refund.external_refund_id = result.external_refund_id or refund.external_refund_id
        refund.provider_status = result.status
        refund.last_provider_sync_at = datetime.now(UTC)
        target = self._map_provider_status(result.status)
        if target is None:
            if refund.status in FINAL_REFUND_STATUSES:
                refund.last_error_code = "payment_refund_provider_status_unknown_final"
                refund.last_error_message = f"Estado provider no mapeado para refund final: {self._sanitize(result.status)}"
                return
            refund.last_error_code = "payment_refund_provider_status_unknown"
            refund.last_error_message = f"Estado provider no mapeado: {self._sanitize(result.status)}"
            self._transition(refund, PaymentRefundStatus.reconcile_required, refund.last_error_code, refund.last_error_message, actor, result.provider_reference)
            return
        if refund.status != target:
            self._transition(refund, target, f"payment_refund_{target.value}", "Estado de reembolso actualizado.", actor, result.provider_reference)
        if target == PaymentRefundStatus.approved:
            refund.processed_at = result.processed_at or datetime.now(UTC)
            self._publish_refund_event("payment.refund.approved", refund)
        elif target == PaymentRefundStatus.rejected:
            self._publish_refund_event("payment.refund.rejected", refund)
        elif target == PaymentRefundStatus.failed:
            refund.failed_at = datetime.now(UTC)
            self._publish_refund_event("payment.refund.failed", refund)

    def _refresh_order_refund_summary(self, order: PaymentOrder) -> None:
        self.db.flush()
        approved = self._approved_sum(order.id)
        pending = self.db.scalar(select(func.count(PaymentRefund.id)).where(PaymentRefund.payment_order_id == order.id, PaymentRefund.status.in_([PaymentRefundStatus.requested, PaymentRefundStatus.processing, PaymentRefundStatus.reconcile_required]))) or 0
        failed = self.db.scalar(select(func.count(PaymentRefund.id)).where(PaymentRefund.payment_order_id == order.id, PaymentRefund.status.in_([PaymentRefundStatus.failed, PaymentRefundStatus.rejected]))) or 0
        order.refunded_amount = approved
        order.refund_status = self._summary_status(order, approved, pending=pending, failed=failed)
        if approved > 0:
            order.last_refunded_at = datetime.now(UTC)
        if approved == order.amount and order.status == PaymentOrderStatus.approved:
            order.status = PaymentOrderStatus.refunded

    @staticmethod
    def _summary_status(order: PaymentOrder, approved: Decimal, *, pending: int = 0, failed: int = 0) -> str:
        if approved >= order.amount:
            return "refunded"
        if approved > 0:
            return "partially_refunded"
        if pending:
            return "refund_pending"
        if failed:
            return "refund_failed"
        return "not_refunded"

    def _approved_sum(self, payment_order_id: int) -> Decimal:
        return self.db.scalar(select(func.coalesce(func.sum(PaymentRefund.amount), 0)).where(PaymentRefund.payment_order_id == payment_order_id, PaymentRefund.status == PaymentRefundStatus.approved)) or Decimal("0")

    def _order(self, payment_order_id: int, *, lock: bool = False) -> PaymentOrder:
        query = select(PaymentOrder).where(PaymentOrder.id == payment_order_id)
        if lock:
            query = query.with_for_update()
        order = self.db.scalar(query)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        return order

    def _mercado_pago_integration(self, *, require_enabled: bool = True) -> Integration:
        query = select(Integration).where(Integration.integration_type == IntegrationType.payment, Integration.provider == IntegrationProvider.mercado_pago)
        if require_enabled:
            query = query.where(Integration.enabled.is_(True))
        integration = self.db.scalar(query.order_by(Integration.id.desc()).limit(1))
        if not integration:
            raise PaymentProviderError("Mercado Pago no configurado.", code="mercado_pago_integration_not_configured")
        return integration

    def _transition(self, refund: PaymentRefund, new_status: PaymentRefundStatus, reason_code: str, reason_summary: str, actor: User | None, provider_reference: dict | None) -> None:
        previous = refund.status
        if previous == new_status:
            return
        refund.status = new_status
        self._add_history(refund, previous, new_status, reason_code, reason_summary, actor, provider_reference)

    def _add_history(self, refund: PaymentRefund, previous: PaymentRefundStatus | None, new_status: PaymentRefundStatus, reason_code: str, reason_summary: str, actor: User | None, provider_reference: dict | None) -> None:
        self.db.add(PaymentRefundStatusHistory(refund_id=refund.id, previous_status=previous.value if previous else None, new_status=new_status.value, reason_code=self._sanitize(reason_code)[:120], reason_summary=self._sanitize(reason_summary), changed_by_user_id=actor.id if actor else None, provider_reference=self._safe_reference(provider_reference), created_at=datetime.now(UTC)))

    def _publish_refund_event(self, event_type: str, refund: PaymentRefund) -> None:
        existing = self.db.scalar(select(AuditLog).where(AuditLog.entity_name == "PaymentRefund", AuditLog.entity_id == str(refund.id), AuditLog.action == event_type.replace(".", "_")))
        if existing:
            return
        self.db.add(AuditLog(user_id=None, action=event_type.replace(".", "_"), entity_name="PaymentRefund", entity_id=str(refund.id), metadata_json={"schema_version": "1.0", "event_type": event_type, "event_id": f"evt_refund_{refund.id}_{event_type.split('.')[-1]}", "occurred_at": datetime.now(UTC).isoformat(), "refund": {"id": refund.id, "payment_order_id": refund.payment_order_id, "amount": str(refund.amount), "currency": refund.currency.value, "status": refund.status.value}}, created_at=datetime.now(UTC)))

    @staticmethod
    def _map_provider_status(value: str) -> PaymentRefundStatus | None:
        mapping = {"approved": PaymentRefundStatus.approved, "refunded": PaymentRefundStatus.approved, "pending": PaymentRefundStatus.processing, "processing": PaymentRefundStatus.processing, "in_process": PaymentRefundStatus.processing, "rejected": PaymentRefundStatus.rejected, "cancelled": PaymentRefundStatus.cancelled, "failed": PaymentRefundStatus.failed}
        return mapping.get((value or "").strip().lower())

    @staticmethod
    def _validate_amount(amount: Decimal, currency: PaymentCurrency) -> None:
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_refund_amount_must_be_positive"})
        if currency == PaymentCurrency.CLP and amount != amount.to_integral_value():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_refund_currency_clp_requires_integer_amount"})

    @staticmethod
    def _fingerprint(payload: dict) -> str:
        normalized = {key: (str(value) if isinstance(value, Decimal) else value.value if hasattr(value, "value") else value) for key, value in payload.items()}
        return sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _sanitize(value: str | None) -> str:
        text = (value or "").strip()
        text = re.sub(r"(?i)(token|secret|password|authorization|bearer)\s*[:=]\s*\S+", r"\1=[redacted]", text)
        return text[:300]

    @staticmethod
    def _safe_reference(reference: dict | None) -> dict | None:
        if not reference:
            return None
        return {str(key)[:80]: str(value)[:160] if value is not None else None for key, value in reference.items()}


