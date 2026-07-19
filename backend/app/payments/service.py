from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.models.integration import Integration
from app.models.payment import PaymentOrder, PaymentOrderStatusHistory
from app.models.professional_profile import PaymentTiming, ProfessionalProfile
from app.models.user import User, UserRole
from app.payments.contracts import PaymentCreateInput, PaymentProviderError, PaymentProviderHealth
from app.payments.enums import PaymentCurrency, PaymentOrderStatus, PaymentProviderKey
from app.payments.registry import PaymentProviderNotImplementedError, payment_provider_registry
from app.payments.schemas import PaymentCheckoutRead, PaymentOrderCancel, PaymentOrderCreate
from app.payments.transitions import ACTIVE_PAYMENT_STATUSES, FINAL_PAYMENT_STATUSES, can_transition
from app.payments.providers.mercado_pago import (
    build_preference_payload,
    map_mercado_pago_status,
    mercado_pago_client_factory,
    parse_mercado_pago_config,
    resolve_secret_reference,
)


class PaymentOrderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_admin(
        self,
        *,
        status_filter: PaymentOrderStatus | None = None,
        provider: PaymentProviderKey | None = None,
        appointment_id: int | None = None,
        client_id: int | None = None,
        professional_id: int | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PaymentOrder], int]:
        query = select(PaymentOrder)
        count_query = select(func.count(PaymentOrder.id))
        conditions = []
        if status_filter:
            conditions.append(PaymentOrder.status == status_filter)
        if provider:
            conditions.append(PaymentOrder.provider == provider)
        if appointment_id:
            conditions.append(PaymentOrder.appointment_id == appointment_id)
        if client_id:
            conditions.append(PaymentOrder.client_id == client_id)
        if professional_id:
            conditions.append(PaymentOrder.professional_id == professional_id)
        if search:
            term = f"%{search.strip()}%"
            conditions.append(or_(PaymentOrder.description.ilike(term), PaymentOrder.external_payment_id.ilike(term)))
        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        total = self.db.scalar(count_query) or 0
        items = list(self.db.scalars(query.order_by(PaymentOrder.created_at.desc(), PaymentOrder.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return items, total

    def get(self, payment_order_id: int) -> PaymentOrder:
        item = self.db.get(PaymentOrder, payment_order_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        return item

    def list_for_professional(self, user: User) -> list[PaymentOrder]:
        professional = self._professional_for_user(user)
        return list(
            self.db.scalars(
                select(PaymentOrder)
                .where(PaymentOrder.professional_id == professional.id)
                .order_by(PaymentOrder.created_at.desc(), PaymentOrder.id.desc())
            )
        )

    def get_for_professional(self, payment_order_id: int, user: User) -> PaymentOrder:
        item = self.get(payment_order_id)
        professional = self._professional_for_user(user)
        if item.professional_id != professional.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        return item

    def list_for_client(self, user: User) -> list[PaymentOrder]:
        client = self._client_for_user(user)
        return list(
            self.db.scalars(
                select(PaymentOrder)
                .where(PaymentOrder.client_id == client.id)
                .order_by(PaymentOrder.created_at.desc(), PaymentOrder.id.desc())
            )
        )

    def get_for_client(self, payment_order_id: int, user: User) -> PaymentOrder:
        item = self.get(payment_order_id)
        client = self._client_for_user(user)
        if item.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        return item

    def list_history(self, payment_order_id: int) -> list[PaymentOrderStatusHistory]:
        return list(
            self.db.scalars(
                select(PaymentOrderStatusHistory)
                .where(PaymentOrderStatusHistory.payment_order_id == payment_order_id)
                .order_by(PaymentOrderStatusHistory.created_at.asc(), PaymentOrderStatusHistory.id.asc())
            )
        )

    def latest_for_appointment(self, appointment_id: int) -> PaymentOrder | None:
        return self.db.scalar(
            select(PaymentOrder)
            .where(PaymentOrder.appointment_id == appointment_id)
            .order_by(PaymentOrder.created_at.desc(), PaymentOrder.id.desc())
            .limit(1)
        )

    def create(self, payload: PaymentOrderCreate, actor: User, idempotency_key: str | None = None, *, commit: bool = True) -> PaymentOrder:
        resolved = self._resolve_payload(payload)
        fingerprint = self._fingerprint(resolved)
        generated_key = idempotency_key is None
        key = idempotency_key or self._generated_idempotency_key(resolved, fingerprint)
        if key:
            existing = self.db.scalar(select(PaymentOrder).where(PaymentOrder.idempotency_key == key))
            if existing:
                if existing.request_fingerprint != fingerprint:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_idempotency_conflict"})
                if generated_key and existing.status in FINAL_PAYMENT_STATUSES:
                    key = None
                else:
                    return existing
        if resolved["appointment_id"] is not None:
            self._ensure_no_blocking_order(resolved["appointment_id"])
        item = PaymentOrder(
            appointment_id=resolved["appointment_id"],
            client_id=resolved["client_id"],
            professional_id=resolved["professional_id"],
            specialty_id=resolved["specialty_id"],
            provider=resolved["provider"],
            amount=resolved["amount"],
            currency=resolved["currency"],
            description=resolved["description"],
            expires_at=resolved["expires_at"],
            idempotency_key=key,
            request_fingerprint=fingerprint,
            created_by_user_id=actor.id,
        )
        self.db.add(item)
        try:
            self.db.flush()
            self._add_history(item, None, item.status, "payment_order_created", "Orden de pago creada.", actor, None)
            self._audit(actor, "payment_order_created", item, {"status": item.status.value, "provider": item.provider.value})
            self._audit(actor, "payment_order_event", item, {"event_type": "payment.order.created", "payment_order_id": item.id, "appointment_id": item.appointment_id, "status": item.status.value})
            if commit:
                self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_idempotency_conflict"}) from exc
        if commit:
            self.db.refresh(item)
        return item

    async def submit(self, payment_order_id: int, actor: User, idempotency_key: str | None = None) -> PaymentOrder:
        item = self.get(payment_order_id)
        if item.provider == PaymentProviderKey.mercado_pago:
            return self.submit_mercado_pago(item, actor, idempotency_key)
        if item.external_payment_id and item.status == PaymentOrderStatus.pending:
            return item
        self._ensure_transition(item.status, PaymentOrderStatus.pending)
        provider = self._provider(item.provider)
        key = idempotency_key or item.idempotency_key or f"payment-submit:{item.id}:{item.request_fingerprint}"
        try:
            result = await provider.create_payment(
                PaymentCreateInput(
                    amount=item.amount,
                    currency=item.currency,
                    description=item.description or f"Orden de pago #{item.id}",
                    idempotency_key=key,
                    expires_at=item.expires_at,
                )
            )
        except PaymentProviderError as exc:
            self._fail_provider_error(item, actor, exc.code, exc.message)
            return item
        item.external_payment_id = result.external_payment_id
        item.expires_at = result.expires_at or item.expires_at
        self._transition(item, PaymentOrderStatus.pending, "payment_submitted", "Orden enviada al provider.", actor, result.provider_reference)
        self.db.commit()
        self.db.refresh(item)
        return item

    def submit_mercado_pago(self, item: PaymentOrder, actor: User, idempotency_key: str | None = None) -> PaymentOrder:
        if item.external_preference_id and item.checkout_url and item.status in {PaymentOrderStatus.pending, PaymentOrderStatus.requires_action}:
            return item
        if item.status == PaymentOrderStatus.draft:
            self._transition(item, PaymentOrderStatus.pending, "mercado_pago_payment_submitted", "Orden preparada para Checkout Pro.", actor, {"provider": "mercado_pago"})
        elif item.status not in {PaymentOrderStatus.pending, PaymentOrderStatus.requires_action}:
            self._ensure_transition(item.status, PaymentOrderStatus.pending)
        integration = self._mercado_pago_integration()
        config = parse_mercado_pago_config(integration)
        token = resolve_secret_reference(config["access_token_reference"])
        payer_email = item.client.user.email if item.client and item.client.user else None
        payload = build_preference_payload(
            order_id=item.id,
            appointment_id=item.appointment_id,
            amount=item.amount,
            currency=item.currency,
            description=item.description or "Reserva RealMeet",
            config=config,
            payer_email=payer_email,
        )
        key = idempotency_key or f"{item.idempotency_key or f'payment-order:{item.id}'}:mercado-pago:create-preference"
        try:
            result = mercado_pago_client_factory(token).create_preference(payload, idempotency_key=key)
        except Exception as exc:
            self._fail_provider_error(item, actor, "mercado_pago_preference_failed", self._sanitize(str(exc)) or "No se pudo crear preferencia Mercado Pago.")
            return item
        item.external_preference_id = result.preference_id
        item.checkout_url = result.init_point
        item.sandbox_checkout_url = result.sandbox_init_point
        item.provider_status = result.status or "pending"
        item.last_provider_sync_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        return item

    async def cancel(self, payment_order_id: int, actor: User, payload: PaymentOrderCancel | None = None) -> PaymentOrder:
        item = self.get(payment_order_id)
        if item.external_payment_id:
            provider = self._provider(item.provider)
            try:
                result = await provider.cancel_payment(item.external_payment_id)
                reference = result.provider_reference
            except PaymentProviderError as exc:
                self._fail_provider_error(item, actor, exc.code, exc.message)
                return item
        else:
            reference = None
        self._transition(item, PaymentOrderStatus.cancelled, "payment_cancelled", payload.reason if payload and payload.reason else "Orden cancelada.", actor, reference)
        item.cancelled_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        return item

    def fake_approve(self, payment_order_id: int, actor: User) -> PaymentOrder:
        item = self._fake_item(payment_order_id)
        if item.status == PaymentOrderStatus.approved:
            return item
        self._ensure_not_expired(item, actor)
        if item.status == PaymentOrderStatus.draft:
            self._transition(item, PaymentOrderStatus.pending, "fake_payment_submitted", "Orden fake preparada para checkout.", actor, {"provider": "fake", "operation": "submit"})
        self._transition(item, PaymentOrderStatus.approved, "fake_payment_approved", "Pago fake aprobado.", actor, {"provider": "fake", "operation": "approve"})
        item.paid_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        self._apply_approved_policy(item, actor)
        self._publish_payment_event("payment.approved", item)
        return item

    def fake_reject(self, payment_order_id: int, actor: User) -> PaymentOrder:
        item = self._fake_item(payment_order_id)
        if item.status == PaymentOrderStatus.rejected:
            return item
        if item.status == PaymentOrderStatus.draft:
            self._transition(item, PaymentOrderStatus.pending, "fake_payment_submitted", "Orden fake preparada para checkout.", actor, {"provider": "fake", "operation": "submit"})
        self._transition(item, PaymentOrderStatus.rejected, "fake_payment_rejected", "Pago fake rechazado.", actor, {"provider": "fake", "operation": "reject"})
        item.rejected_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        self._apply_rejected_policy(item, actor)
        self._publish_payment_event("payment.rejected", item)
        return item

    def fake_expire(self, payment_order_id: int, actor: User) -> PaymentOrder:
        item = self._fake_item(payment_order_id)
        if item.status == PaymentOrderStatus.expired:
            return item
        if item.status == PaymentOrderStatus.draft:
            self._transition(item, PaymentOrderStatus.pending, "fake_payment_submitted", "Orden fake preparada para expiracion.", actor, {"provider": "fake", "operation": "submit"})
        self._transition(item, PaymentOrderStatus.expired, "fake_payment_expired", "Pago fake expirado.", actor, {"provider": "fake", "operation": "expire"})
        self.db.commit()
        self.db.refresh(item)
        self._apply_expired_policy(item, actor)
        self._publish_payment_event("payment.expired", item)
        return item

    def fake_fail(self, payment_order_id: int, actor: User) -> PaymentOrder:
        item = self._fake_item(payment_order_id)
        item.last_error_code = "fake_payment_failed"
        item.last_error_message = self._sanitize("Fallo fake controlado.")
        item.failed_at = datetime.now(UTC)
        self._transition(item, PaymentOrderStatus.failed, "fake_payment_failed", item.last_error_message, actor, {"provider": "fake", "operation": "fail"})
        self.db.commit()
        self.db.refresh(item)
        return item

    def checkout_for_client(self, payment_order_id: int, user: User) -> PaymentCheckoutRead:
        item = self.get_for_client(payment_order_id, user)
        if item.provider == PaymentProviderKey.mercado_pago:
            if item.status == PaymentOrderStatus.draft or not item.checkout_url:
                self.submit_mercado_pago(item, user)
                item = self.get_for_client(payment_order_id, user)
            checkout_available = item.status in {PaymentOrderStatus.pending, PaymentOrderStatus.requires_action} and bool(item.checkout_url or item.sandbox_checkout_url)
            return PaymentCheckoutRead(
                id=item.id,
                appointment_id=item.appointment_id,
                provider=item.provider,
                description=item.description,
                amount=item.amount,
                currency=item.currency,
                status=item.status,
                expires_at=item.expires_at,
                checkout_available=checkout_available,
                test_environment=False,
                checkout_url=item.checkout_url or item.sandbox_checkout_url,
                message="Seras redirigido a Mercado Pago. RealMeet no procesa tarjetas.",
            )
        if item.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_checkout_provider_not_available"})
        if self._is_expired(item):
            self.fake_expire(item.id, user)
            item = self.get_for_client(payment_order_id, user)
        checkout_available = item.status in ACTIVE_PAYMENT_STATUSES
        return PaymentCheckoutRead(
            id=item.id,
            appointment_id=item.appointment_id,
            provider=item.provider,
            description=item.description,
            amount=item.amount,
            currency=item.currency,
            status=item.status,
            expires_at=item.expires_at,
            checkout_available=checkout_available,
            message="Entorno de prueba: no se realizara un cobro real." if checkout_available else "Checkout no disponible para esta orden.",
        )

    def approve_checkout_for_client(self, payment_order_id: int, user: User) -> PaymentOrder:
        item = self.get_for_client(payment_order_id, user)
        if item.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_checkout_provider_not_available"})
        return self.fake_approve(item.id, user)

    def reject_checkout_for_client(self, payment_order_id: int, user: User) -> PaymentOrder:
        item = self.get_for_client(payment_order_id, user)
        if item.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_checkout_provider_not_available"})
        return self.fake_reject(item.id, user)

    def reconcile(self, payment_order_id: int, actor: User) -> tuple[str, PaymentOrder]:
        item = self.get(payment_order_id)
        refund_result = self._reconcile_refunds(item)
        if refund_result is not None:
            return refund_result, item
        if item.provider == PaymentProviderKey.mercado_pago and item.status in ACTIVE_PAYMENT_STATUSES and item.external_payment_id:
            self.sync_provider(payment_order_id, actor)
            self.db.refresh(item)
            return "provider_sync_required", item
        appointment = item.appointment if item.appointment_id else None
        if not appointment:
            return "manual_review_required", item
        policy = self._appointment_policy(appointment)
        if item.status in ACTIVE_PAYMENT_STATUSES:
            return "payment_not_final", item
        if item.status == PaymentOrderStatus.approved and policy == PaymentTiming.pay_before_confirmation:
            if appointment.status == AppointmentStatus.pending_payment:
                self._confirm_appointment_for_payment(appointment, actor, "Payment reconcile confirmed appointment")
                self.db.refresh(item)
                return "appointment_confirmation_required", item
            if appointment.status == AppointmentStatus.confirmed:
                return "in_sync", item
        if item.status in {PaymentOrderStatus.rejected, PaymentOrderStatus.expired} and appointment.status == AppointmentStatus.pending_payment:
            self._cancel_appointment_for_payment(appointment, actor, "Payment reconcile cancelled pending payment appointment")
            self.db.refresh(item)
            return "appointment_cancellation_required", item
        if item.status == PaymentOrderStatus.approved and appointment.status == AppointmentStatus.confirmed:
            return "in_sync", item
        return "manual_review_required", item

    def _reconcile_refunds(self, item: PaymentOrder) -> str | None:
        from app.models.payment import PaymentRefund, PaymentRefundStatus

        refunds_count = self.db.scalar(select(func.count(PaymentRefund.id)).where(PaymentRefund.payment_order_id == item.id)) or 0
        if not refunds_count:
            return None
        approved = self.db.scalar(select(func.coalesce(func.sum(PaymentRefund.amount), 0)).where(PaymentRefund.payment_order_id == item.id, PaymentRefund.status == PaymentRefundStatus.approved)) or Decimal("0")
        if approved > item.amount:
            return "refund_amount_inconsistent"
        pending = self.db.scalar(select(func.count(PaymentRefund.id)).where(PaymentRefund.payment_order_id == item.id, PaymentRefund.status.in_([PaymentRefundStatus.requested, PaymentRefundStatus.processing, PaymentRefundStatus.reconcile_required]))) or 0
        failed = self.db.scalar(select(func.count(PaymentRefund.id)).where(PaymentRefund.payment_order_id == item.id, PaymentRefund.status.in_([PaymentRefundStatus.failed, PaymentRefundStatus.rejected]))) or 0
        expected = "refunded" if approved >= item.amount else "partially_refunded" if approved > 0 else "refund_pending" if pending else "refund_failed" if failed else "not_refunded"
        expected_order_status = PaymentOrderStatus.refunded if approved >= item.amount else item.status
        if item.refunded_amount != approved or item.refund_status != expected or item.status != expected_order_status:
            item.refunded_amount = approved
            item.refund_status = expected
            if approved > 0:
                item.last_refunded_at = datetime.now(UTC)
            if approved >= item.amount:
                item.status = PaymentOrderStatus.refunded
            self.db.commit()
            self.db.refresh(item)
            return "refund_sync_required"
        if approved >= item.amount:
            return "full_refund_in_sync"
        if approved > 0:
            return "partial_refund_in_sync"
        return None

    async def health(self, provider: PaymentProviderKey) -> PaymentProviderHealth:
        if provider == PaymentProviderKey.mercado_pago:
            integration = self._mercado_pago_integration()
            config = parse_mercado_pago_config(integration)
            token = resolve_secret_reference(config["access_token_reference"])
            result = mercado_pago_client_factory(token).health_check()
            return PaymentProviderHealth(healthy=result.healthy, code=result.code, message=result.message)
        return await self._provider(provider).health_check()

    def sync_provider(self, payment_order_id: int, actor: User) -> PaymentOrder:
        item = self.get(payment_order_id)
        if item.provider != PaymentProviderKey.mercado_pago:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_provider_not_mercado_pago"})
        if not item.external_payment_id:
            item.last_error_code = "provider_payment_not_found"
            item.last_error_message = "Mercado Pago payment id no disponible."
            self.db.commit()
            self.db.refresh(item)
            return item
        integration = self._mercado_pago_integration(require_enabled=False)
        config = parse_mercado_pago_config(integration)
        token = resolve_secret_reference(config["access_token_reference"])
        try:
            result = mercado_pago_client_factory(token).get_payment(item.external_payment_id)
        except Exception as exc:
            item.last_error_code = "mercado_pago_sync_failed"
            item.last_error_message = self._sanitize(str(exc)) or "No se pudo sincronizar Mercado Pago."
            self.db.commit()
            self.db.refresh(item)
            return item
        self.apply_mercado_pago_payment(result, actor)
        return self.get(payment_order_id)

    def apply_mercado_pago_payment(self, result, actor: User | None = None) -> PaymentOrder | None:
        item = self._find_mercado_pago_order(result)
        if not item:
            return None
        item.external_payment_id = result.payment_id
        item.external_preference_id = item.external_preference_id or result.preference_id
        item.provider_status = result.status
        item.provider_status_detail = result.status_detail
        item.last_provider_sync_at = datetime.now(UTC)
        target = map_mercado_pago_status(result.status)
        if target is None:
            item.last_error_code = "payment_provider_status_unknown"
            item.last_error_message = f"Estado Mercado Pago no mapeado: {self._sanitize(result.status)}"
            self.db.commit()
            self.db.refresh(item)
            return item
        if item.status == target:
            self.db.commit()
            self.db.refresh(item)
            return item
        if item.status == PaymentOrderStatus.draft and target != PaymentOrderStatus.pending:
            self._transition(item, PaymentOrderStatus.pending, "mercado_pago_payment_submitted", "Orden sincronizada desde Mercado Pago.", actor, result.provider_reference)
        if item.status not in FINAL_PAYMENT_STATUSES:
            self._transition(item, target, f"mercado_pago_payment_{target.value}", "Estado confirmado via API Mercado Pago.", actor, result.provider_reference)
            now = datetime.now(UTC)
            if target == PaymentOrderStatus.approved:
                item.paid_at = item.paid_at or now
            if target == PaymentOrderStatus.rejected:
                item.rejected_at = item.rejected_at or now
            if target == PaymentOrderStatus.cancelled:
                item.cancelled_at = item.cancelled_at or now
            if target == PaymentOrderStatus.failed:
                item.failed_at = item.failed_at or now
        self.db.commit()
        self.db.refresh(item)
        if target == PaymentOrderStatus.approved:
            self._apply_approved_policy(item, actor)
            self._publish_payment_event("payment.approved", item)
        elif target == PaymentOrderStatus.rejected:
            self._apply_rejected_policy(item, actor)
            self._publish_payment_event("payment.rejected", item)
        elif target in {PaymentOrderStatus.cancelled, PaymentOrderStatus.expired}:
            self._apply_expired_policy(item, actor)
            self._publish_payment_event("payment.expired", item)
        return item

    def _resolve_payload(self, payload: PaymentOrderCreate) -> dict:
        currency = PaymentCurrency(payload.currency)
        if currency != PaymentCurrency.CLP:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_currency_not_supported"})
        appointment = self.db.get(Appointment, payload.appointment_id) if payload.appointment_id else None
        amount = payload.amount
        client_id = payload.client_id
        professional_id = payload.professional_id
        specialty_id = payload.specialty_id
        description = payload.description
        if appointment:
            client_id = client_id or appointment.client_id
            professional_id = professional_id or appointment.professional_id
            specialty_id = specialty_id or appointment.specialty_id
            if client_id != appointment.client_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_client_mismatch"})
            if professional_id != appointment.professional_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_professional_mismatch"})
            professional = self.db.get(ProfessionalProfile, appointment.professional_id)
            if amount is None and professional and professional.price:
                amount = professional.price
            description = description or f"Reserva #{appointment.id}"
        elif payload.appointment_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if amount is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_amount_required"})
        self._validate_amount(amount, currency)
        return {
            "appointment_id": payload.appointment_id,
            "client_id": client_id,
            "professional_id": professional_id,
            "specialty_id": specialty_id,
            "provider": payload.provider,
            "amount": amount,
            "currency": currency,
            "description": description,
            "expires_at": payload.expires_at,
        }

    def _ensure_no_blocking_order(self, appointment_id: int) -> None:
        existing = self.db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.appointment_id == appointment_id,
                PaymentOrder.status.in_([*ACTIVE_PAYMENT_STATUSES, PaymentOrderStatus.approved]),
            )
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_active_order_exists"})

    def _fake_item(self, payment_order_id: int) -> PaymentOrder:
        item = self.get(payment_order_id)
        if item.provider != PaymentProviderKey.fake:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_provider_not_fake"})
        return item

    def _ensure_not_expired(self, item: PaymentOrder, actor: User) -> None:
        if self._is_expired(item):
            self.fake_expire(item.id, actor)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_order_expired"})

    @staticmethod
    def _is_expired(item: PaymentOrder) -> bool:
        return bool(item.expires_at and item.expires_at <= datetime.now(UTC) and item.status in ACTIVE_PAYMENT_STATUSES)

    def _provider(self, provider: PaymentProviderKey):
        try:
            return payment_provider_registry.resolve(provider)
        except PaymentProviderNotImplementedError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": exc.code}) from exc

    def _mercado_pago_integration(self, *, require_enabled: bool = True) -> Integration:
        query = select(Integration).where(
            Integration.integration_type == IntegrationType.payment,
            Integration.provider == IntegrationProvider.mercado_pago,
        )
        if require_enabled:
            query = query.where(Integration.enabled.is_(True))
        integration = self.db.scalar(query.order_by(Integration.id.desc()).limit(1))
        if not integration:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "mercado_pago_integration_not_configured"})
        return integration

    def _find_mercado_pago_order(self, result) -> PaymentOrder | None:
        if result.metadata_payment_order_id:
            item = self.db.get(PaymentOrder, result.metadata_payment_order_id)
            if item and item.provider == PaymentProviderKey.mercado_pago:
                return item
        if result.external_reference and result.external_reference.startswith("payment-order-"):
            raw_id = result.external_reference.removeprefix("payment-order-")
            if raw_id.isdigit():
                item = self.db.get(PaymentOrder, int(raw_id))
                if item and item.provider == PaymentProviderKey.mercado_pago:
                    return item
        if result.payment_id:
            return self.db.scalar(select(PaymentOrder).where(PaymentOrder.external_payment_id == result.payment_id, PaymentOrder.provider == PaymentProviderKey.mercado_pago))
        return None

    def _transition(
        self,
        item: PaymentOrder,
        new_status: PaymentOrderStatus,
        reason_code: str,
        reason_summary: str,
        actor: User | None,
        provider_reference: dict | None,
    ) -> None:
        self._ensure_transition(item.status, new_status)
        previous = item.status
        item.status = new_status
        self._add_history(item, previous, new_status, reason_code, reason_summary, actor, provider_reference)
        self._audit(actor, "payment_order_status_changed", item, {"from": previous.value, "to": new_status.value, "reason": reason_code})

    def _apply_approved_policy(self, item: PaymentOrder, actor: User) -> None:
        appointment = item.appointment if item.appointment_id else None
        if not appointment:
            return
        if self._appointment_policy(appointment) == PaymentTiming.pay_before_confirmation and appointment.status == AppointmentStatus.pending_payment:
            self._confirm_appointment_for_payment(appointment, actor, "Payment approved")

    def _apply_rejected_policy(self, item: PaymentOrder, actor: User) -> None:
        appointment = item.appointment if item.appointment_id else None
        if appointment and appointment.status == AppointmentStatus.pending_payment:
            self._cancel_appointment_for_payment(appointment, actor, "Payment rejected")

    def _apply_expired_policy(self, item: PaymentOrder, actor: User) -> None:
        appointment = item.appointment if item.appointment_id else None
        if appointment and appointment.status == AppointmentStatus.pending_payment:
            self._cancel_appointment_for_payment(appointment, actor, "Payment expired")

    def _confirm_appointment_for_payment(self, appointment: Appointment, actor: User | None, reason: str) -> None:
        from app.services.appointments import AppointmentService

        AppointmentService(self.db).confirm_after_payment(appointment, actor or self._system_actor(appointment), reason)

    def _cancel_appointment_for_payment(self, appointment: Appointment, actor: User | None, reason: str) -> None:
        from app.services.appointments import AppointmentService

        AppointmentService(self.db).cancel_after_payment_failure(appointment, actor or self._system_actor(appointment), reason)

    def _system_actor(self, appointment: Appointment) -> User:
        user = self.db.get(User, appointment.client.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_actor_not_found"})
        return user

    @staticmethod
    def _appointment_policy(appointment: Appointment) -> PaymentTiming:
        professional = getattr(appointment, "professional", None)
        return getattr(professional, "payment_timing", PaymentTiming.no_payment) or PaymentTiming.no_payment

    def _publish_payment_event(self, event_type: str, item: PaymentOrder) -> None:
        existing = self.db.scalar(
            select(AuditLog).where(
                AuditLog.entity_name == "PaymentOrder",
                AuditLog.entity_id == str(item.id),
                AuditLog.action == event_type.replace(".", "_"),
            )
        )
        if existing:
            return
        self.db.add(
            AuditLog(
                user_id=None,
                action=event_type.replace(".", "_"),
                entity_name="PaymentOrder",
                entity_id=str(item.id),
                metadata_json={
                    "event_type": event_type,
                    "payment_order_id": item.id,
                    "appointment_id": item.appointment_id,
                    "status": item.status.value,
                    "amount": str(item.amount),
                    "currency": item.currency.value,
                },
                created_at=datetime.now(UTC),
            )
        )
        self.db.commit()

    @staticmethod
    def _ensure_transition(previous: PaymentOrderStatus, new: PaymentOrderStatus) -> None:
        if previous in FINAL_PAYMENT_STATUSES or not can_transition(previous, new):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "payment_invalid_status_transition"})

    def _fail_provider_error(self, item: PaymentOrder, actor: User | None, code: str, message: str) -> None:
        item.last_error_code = self._sanitize(code)[:120]
        item.last_error_message = self._sanitize(message)
        item.failed_at = datetime.now(UTC)
        self._transition(item, PaymentOrderStatus.failed, item.last_error_code, item.last_error_message, actor, {"provider": item.provider.value})
        self.db.commit()
        self.db.refresh(item)

    def _add_history(
        self,
        item: PaymentOrder,
        previous: PaymentOrderStatus | None,
        new: PaymentOrderStatus,
        reason_code: str,
        reason_summary: str,
        actor: User | None,
        provider_reference: dict | None,
    ) -> None:
        self.db.add(
            PaymentOrderStatusHistory(
                payment_order_id=item.id,
                previous_status=previous.value if previous else None,
                new_status=new.value,
                reason_code=self._sanitize(reason_code)[:120],
                reason_summary=self._sanitize(reason_summary),
                changed_by_user_id=actor.id if actor else None,
                provider_reference=self._safe_reference(provider_reference),
                created_at=datetime.now(UTC),
            )
        )

    def _audit(self, actor: User | None, action: str, item: PaymentOrder, metadata: dict) -> None:
        self.db.add(
            AuditLog(
                user_id=actor.id if actor else None,
                action=action,
                entity_name="PaymentOrder",
                entity_id=str(item.id),
                metadata_json=metadata,
                created_at=datetime.now(UTC),
            )
        )

    @staticmethod
    def _validate_amount(amount: Decimal, currency: PaymentCurrency) -> None:
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_amount_must_be_positive"})
        if currency == PaymentCurrency.CLP and amount != amount.to_integral_value():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "payment_currency_clp_requires_integer_amount"})

    @staticmethod
    def _fingerprint(payload: dict) -> str:
        normalized = {
            key: (str(value) if isinstance(value, Decimal) else value.value if hasattr(value, "value") else value.isoformat() if isinstance(value, datetime) else value)
            for key, value in payload.items()
        }
        return sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _generated_idempotency_key(payload: dict, fingerprint: str) -> str | None:
        if payload["appointment_id"] is None:
            return None
        return f"payment-order:appointment:{payload['appointment_id']}:{fingerprint[:32]}"

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

    def _professional_for_user(self, user: User) -> ProfessionalProfile:
        if user.role != UserRole.professional:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        profile = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional profile not found")
        return profile

    def _client_for_user(self, user: User) -> ClientProfile:
        if user.role != UserRole.client:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        profile = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found")
        return profile
