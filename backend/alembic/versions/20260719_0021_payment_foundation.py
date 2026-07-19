"""add payment foundation

Revision ID: 20260719_0021
Revises: 20260718_0020
Create Date: 2026-07-19 00:21:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260719_0021"
down_revision: str | None = "20260718_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    payment_provider = postgresql.ENUM("fake", "mercado_pago", "stripe", name="payment_provider")
    payment_status = postgresql.ENUM("draft", "pending", "requires_action", "approved", "rejected", "cancelled", "expired", "failed", "refunded", name="payment_order_status")
    payment_currency = postgresql.ENUM("CLP", name="payment_currency")
    for enum_type in (payment_provider, payment_status, payment_currency):
        enum_type.create(op.get_bind(), checkfirst=True)

    payment_provider_ref = postgresql.ENUM(name="payment_provider", create_type=False)
    payment_status_ref = postgresql.ENUM(name="payment_order_status", create_type=False)
    payment_currency_ref = postgresql.ENUM(name="payment_currency", create_type=False)

    op.create_table(
        "payment_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("professional_id", sa.Integer(), nullable=True),
        sa.Column("specialty_id", sa.Integer(), nullable=True),
        sa.Column("provider", payment_provider_ref, nullable=False),
        sa.Column("external_payment_id", sa.String(length=180), nullable=True),
        sa.Column("idempotency_key", sa.String(length=220), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("status", payment_status_ref, server_default="draft", nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", payment_currency_ref, server_default="CLP", nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.String(length=300), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_payment_orders_amount_positive"),
        sa.CheckConstraint("currency <> 'CLP' OR amount = trunc(amount)", name="ck_payment_orders_clp_integer"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["client_id"], ["client_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["professional_id"], ["professional_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["specialty_id"], ["specialties.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_orders_appointment", "payment_orders", ["appointment_id"])
    op.create_index("ix_payment_orders_client", "payment_orders", ["client_id"])
    op.create_index("ix_payment_orders_professional", "payment_orders", ["professional_id"])
    op.create_index("ix_payment_orders_status", "payment_orders", ["status"])
    op.create_index("ix_payment_orders_provider", "payment_orders", ["provider"])
    op.create_index("ix_payment_orders_idempotency", "payment_orders", ["idempotency_key"], unique=True)
    op.create_index(
        "uq_payment_orders_one_active_per_appointment",
        "payment_orders",
        ["appointment_id"],
        unique=True,
        postgresql_where=sa.text("appointment_id IS NOT NULL AND status IN ('draft', 'pending', 'requires_action', 'approved')"),
    )

    op.create_table(
        "payment_order_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_order_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("reason_code", sa.String(length=120), nullable=True),
        sa.Column("reason_summary", sa.Text(), nullable=True),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("provider_reference", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_order_id"], ["payment_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_order_status_history_order", "payment_order_status_history", ["payment_order_id"])
    op.create_index("ix_payment_order_status_history_created", "payment_order_status_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_payment_order_status_history_created", table_name="payment_order_status_history")
    op.drop_index("ix_payment_order_status_history_order", table_name="payment_order_status_history")
    op.drop_table("payment_order_status_history")
    op.drop_index("uq_payment_orders_one_active_per_appointment", table_name="payment_orders")
    op.drop_index("ix_payment_orders_idempotency", table_name="payment_orders")
    op.drop_index("ix_payment_orders_provider", table_name="payment_orders")
    op.drop_index("ix_payment_orders_status", table_name="payment_orders")
    op.drop_index("ix_payment_orders_professional", table_name="payment_orders")
    op.drop_index("ix_payment_orders_client", table_name="payment_orders")
    op.drop_index("ix_payment_orders_appointment", table_name="payment_orders")
    op.drop_table("payment_orders")
    for enum_name in ("payment_currency", "payment_order_status", "payment_provider"):
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
