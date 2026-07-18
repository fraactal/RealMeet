from datetime import datetime
from decimal import Decimal

import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.payments.enums import PaymentCurrency, PaymentOrderStatus, PaymentProviderKey


ACTIVE_PAYMENT_STATUSES = ("draft", "pending", "requires_action", "approved")


class PaymentOrder(Base, TimestampMixin):
    __tablename__ = "payment_orders"
    __table_args__ = (
        Index("ix_payment_orders_appointment", "appointment_id"),
        Index("ix_payment_orders_client", "client_id"),
        Index("ix_payment_orders_professional", "professional_id"),
        Index("ix_payment_orders_status", "status"),
        Index("ix_payment_orders_provider", "provider"),
        Index("ix_payment_orders_idempotency", "idempotency_key", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"))
    client_id: Mapped[int | None] = mapped_column(ForeignKey("client_profiles.id", ondelete="SET NULL"))
    professional_id: Mapped[int | None] = mapped_column(ForeignKey("professional_profiles.id", ondelete="SET NULL"))
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id", ondelete="SET NULL"))
    provider: Mapped[PaymentProviderKey] = mapped_column(Enum(PaymentProviderKey, name="payment_provider"), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String(180))
    external_preference_id: Mapped[str | None] = mapped_column(String(180))
    checkout_url: Mapped[str | None] = mapped_column(String(700))
    sandbox_checkout_url: Mapped[str | None] = mapped_column(String(700))
    provider_status: Mapped[str | None] = mapped_column(String(80))
    provider_status_detail: Mapped[str | None] = mapped_column(String(160))
    last_provider_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    refund_status: Mapped[str] = mapped_column(String(40), default="not_refunded", nullable=False)
    last_refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(220))
    request_fingerprint: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[PaymentOrderStatus] = mapped_column(
        Enum(PaymentOrderStatus, name="payment_order_status"),
        default=PaymentOrderStatus.draft,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[PaymentCurrency] = mapped_column(
        Enum(PaymentCurrency, name="payment_currency"),
        default=PaymentCurrency.CLP,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(120))
    last_error_message: Mapped[str | None] = mapped_column(String(300))
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    appointment = relationship("Appointment")
    client = relationship("ClientProfile")
    professional = relationship("ProfessionalProfile")
    history: Mapped[list["PaymentOrderStatusHistory"]] = relationship(
        "PaymentOrderStatusHistory",
        back_populates="payment_order",
        cascade="all, delete-orphan",
    )
    refunds: Mapped[list["PaymentRefund"]] = relationship("PaymentRefund", back_populates="payment_order")

    @property
    def refundable_amount(self) -> Decimal:
        return max(self.amount - self.refunded_amount, Decimal("0"))


class PaymentRefundStatus(str, enum.Enum):
    requested = "requested"
    processing = "processing"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"
    failed = "failed"
    reconcile_required = "reconcile_required"


class PaymentRefundReasonCode(str, enum.Enum):
    appointment_cancelled = "appointment_cancelled"
    duplicate_payment = "duplicate_payment"
    service_not_delivered = "service_not_delivered"
    client_request = "client_request"
    professional_request = "professional_request"
    administrative_adjustment = "administrative_adjustment"
    other = "other"


class PaymentRefund(Base, TimestampMixin):
    __tablename__ = "payment_refunds"
    __table_args__ = (
        Index("ix_payment_refunds_order", "payment_order_id"),
        Index("ix_payment_refunds_status", "status"),
        Index("ix_payment_refunds_idempotency", "idempotency_key", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_order_id: Mapped[int] = mapped_column(ForeignKey("payment_orders.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[PaymentProviderKey] = mapped_column(Enum(PaymentProviderKey, name="payment_provider"), nullable=False)
    external_refund_id: Mapped[str | None] = mapped_column(String(180))
    idempotency_key: Mapped[str | None] = mapped_column(String(220))
    request_fingerprint: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[PaymentRefundStatus] = mapped_column(
        Enum(PaymentRefundStatus, name="payment_refund_status"),
        default=PaymentRefundStatus.requested,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[PaymentCurrency] = mapped_column(Enum(PaymentCurrency, name="payment_currency"), nullable=False)
    reason_code: Mapped[PaymentRefundReasonCode] = mapped_column(Enum(PaymentRefundReasonCode, name="payment_refund_reason_code"), nullable=False)
    reason_summary: Mapped[str | None] = mapped_column(String(255))
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(120))
    last_error_message: Mapped[str | None] = mapped_column(String(300))
    provider_status: Mapped[str | None] = mapped_column(String(80))
    last_provider_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    payment_order: Mapped[PaymentOrder] = relationship("PaymentOrder", back_populates="refunds")
    history: Mapped[list["PaymentRefundStatusHistory"]] = relationship("PaymentRefundStatusHistory", back_populates="refund", cascade="all, delete-orphan")


class PaymentRefundStatusHistory(Base):
    __tablename__ = "payment_refund_status_history"
    __table_args__ = (
        Index("ix_payment_refund_status_history_refund", "refund_id"),
        Index("ix_payment_refund_status_history_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    refund_id: Mapped[int] = mapped_column(ForeignKey("payment_refunds.id", ondelete="CASCADE"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(120))
    reason_summary: Mapped[str | None] = mapped_column(Text)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    provider_reference: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    refund: Mapped[PaymentRefund] = relationship("PaymentRefund", back_populates="history")


class MercadoPagoWebhookProcessingStatus(str, enum.Enum):
    received = "received"
    processed = "processed"
    ignored = "ignored"
    failed = "failed"
    invalid_signature = "invalid_signature"


class MercadoPagoWebhookEvent(Base):
    __tablename__ = "mercado_pago_webhook_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_mercado_pago_webhook_event_id"),
        Index("ix_mercado_pago_webhook_resource", "resource_id"),
        Index("ix_mercado_pago_webhook_payment_order", "payment_order_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(180), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(80))
    resource_id: Mapped[str | None] = mapped_column(String(180))
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_status: Mapped[MercadoPagoWebhookProcessingStatus] = mapped_column(
        Enum(MercadoPagoWebhookProcessingStatus, name="mercado_pago_webhook_processing_status"),
        default=MercadoPagoWebhookProcessingStatus.received,
        nullable=False,
    )
    payment_order_id: Mapped[int | None] = mapped_column(ForeignKey("payment_orders.id", ondelete="SET NULL"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(120))
    error_message: Mapped[str | None] = mapped_column(String(300))

    payment_order = relationship("PaymentOrder")


class PaymentOrderStatusHistory(Base):
    __tablename__ = "payment_order_status_history"
    __table_args__ = (
        Index("ix_payment_order_status_history_order", "payment_order_id"),
        Index("ix_payment_order_status_history_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_order_id: Mapped[int] = mapped_column(ForeignKey("payment_orders.id", ondelete="CASCADE"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(120))
    reason_summary: Mapped[str | None] = mapped_column(Text)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    provider_reference: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    payment_order: Mapped[PaymentOrder] = relationship("PaymentOrder", back_populates="history")
