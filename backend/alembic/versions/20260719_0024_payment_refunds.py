"""add payment refunds

Revision ID: 20260719_0024
Revises: 20260719_0023
Create Date: 2026-07-19 00:24:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260719_0024"
down_revision: str | None = "20260719_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    refund_status = postgresql.ENUM("requested", "processing", "approved", "rejected", "cancelled", "failed", "reconcile_required", name="payment_refund_status")
    refund_reason = postgresql.ENUM("appointment_cancelled", "duplicate_payment", "service_not_delivered", "client_request", "professional_request", "administrative_adjustment", "other", name="payment_refund_reason_code")
    refund_status.create(op.get_bind(), checkfirst=True)
    refund_reason.create(op.get_bind(), checkfirst=True)

    op.add_column("payment_orders", sa.Column("refunded_amount", sa.Numeric(12, 2), server_default="0", nullable=False))
    op.add_column("payment_orders", sa.Column("refund_status", sa.String(length=40), server_default="not_refunded", nullable=False))
    op.add_column("payment_orders", sa.Column("last_refunded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint("ck_payment_orders_refunded_amount_non_negative", "payment_orders", "refunded_amount >= 0")
    op.create_check_constraint("ck_payment_orders_refunded_amount_not_over_amount", "payment_orders", "refunded_amount <= amount")
    op.create_check_constraint("ck_payment_orders_refund_status", "payment_orders", "refund_status IN ('not_refunded','partially_refunded','refunded','refund_pending','refund_failed')")

    status_ref = postgresql.ENUM(name="payment_refund_status", create_type=False)
    reason_ref = postgresql.ENUM(name="payment_refund_reason_code", create_type=False)
    currency_ref = postgresql.ENUM(name="payment_currency", create_type=False)
    provider_ref = postgresql.ENUM(name="payment_provider", create_type=False)
    op.create_table(
        "payment_refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_order_id", sa.Integer(), nullable=False),
        sa.Column("provider", provider_ref, nullable=False),
        sa.Column("external_refund_id", sa.String(length=180), nullable=True),
        sa.Column("idempotency_key", sa.String(length=220), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("status", status_ref, server_default="requested", nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", currency_ref, nullable=False),
        sa.Column("reason_code", reason_ref, nullable=False),
        sa.Column("reason_summary", sa.String(length=255), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.String(length=300), nullable=True),
        sa.Column("provider_status", sa.String(length=80), nullable=True),
        sa.Column("last_provider_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_payment_refunds_amount_positive"),
        sa.CheckConstraint("currency <> 'CLP' OR amount = trunc(amount)", name="ck_payment_refunds_clp_integer"),
        sa.ForeignKeyConstraint(["payment_order_id"], ["payment_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_refunds_order", "payment_refunds", ["payment_order_id"])
    op.create_index("ix_payment_refunds_status", "payment_refunds", ["status"])
    op.create_index("ix_payment_refunds_idempotency", "payment_refunds", ["idempotency_key"], unique=True)

    op.create_table(
        "payment_refund_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("refund_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("reason_code", sa.String(length=120), nullable=True),
        sa.Column("reason_summary", sa.Text(), nullable=True),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("provider_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["refund_id"], ["payment_refunds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_refund_status_history_refund", "payment_refund_status_history", ["refund_id"])
    op.create_index("ix_payment_refund_status_history_created", "payment_refund_status_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_payment_refund_status_history_created", table_name="payment_refund_status_history")
    op.drop_index("ix_payment_refund_status_history_refund", table_name="payment_refund_status_history")
    op.drop_table("payment_refund_status_history")
    op.drop_index("ix_payment_refunds_idempotency", table_name="payment_refunds")
    op.drop_index("ix_payment_refunds_status", table_name="payment_refunds")
    op.drop_index("ix_payment_refunds_order", table_name="payment_refunds")
    op.drop_table("payment_refunds")
    op.drop_constraint("ck_payment_orders_refund_status", "payment_orders", type_="check")
    op.drop_constraint("ck_payment_orders_refunded_amount_not_over_amount", "payment_orders", type_="check")
    op.drop_constraint("ck_payment_orders_refunded_amount_non_negative", "payment_orders", type_="check")
    op.drop_column("payment_orders", "last_refunded_at")
    op.drop_column("payment_orders", "refund_status")
    op.drop_column("payment_orders", "refunded_amount")
    postgresql.ENUM(name="payment_refund_reason_code").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="payment_refund_status").drop(op.get_bind(), checkfirst=True)
