"""add mercado pago checkout pro

Revision ID: 20260719_0023
Revises: 20260719_0022
Create Date: 2026-07-19 00:23:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260719_0023"
down_revision: str | None = "20260719_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE integration_type ADD VALUE IF NOT EXISTS 'payment'")
        op.execute("ALTER TYPE integration_provider ADD VALUE IF NOT EXISTS 'mercado_pago'")

    op.add_column("payment_orders", sa.Column("external_preference_id", sa.String(length=180), nullable=True))
    op.add_column("payment_orders", sa.Column("checkout_url", sa.String(length=700), nullable=True))
    op.add_column("payment_orders", sa.Column("sandbox_checkout_url", sa.String(length=700), nullable=True))
    op.add_column("payment_orders", sa.Column("provider_status", sa.String(length=80), nullable=True))
    op.add_column("payment_orders", sa.Column("provider_status_detail", sa.String(length=160), nullable=True))
    op.add_column("payment_orders", sa.Column("last_provider_sync_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_payment_orders_external_preference", "payment_orders", ["external_preference_id"])
    op.create_index("ix_payment_orders_external_payment", "payment_orders", ["external_payment_id"])

    webhook_status = postgresql.ENUM("received", "processed", "ignored", "failed", "invalid_signature", name="mercado_pago_webhook_processing_status")
    webhook_status.create(op.get_bind(), checkfirst=True)
    webhook_status_ref = postgresql.ENUM(name="mercado_pago_webhook_processing_status", create_type=False)
    op.create_table(
        "mercado_pago_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=180), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.String(length=180), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("processing_status", webhook_status_ref, server_default="received", nullable=False),
        sa.Column("payment_order_id", sa.Integer(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(["payment_order_id"], ["payment_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_mercado_pago_webhook_event_id"),
    )
    op.create_index("ix_mercado_pago_webhook_resource", "mercado_pago_webhook_events", ["resource_id"])
    op.create_index("ix_mercado_pago_webhook_payment_order", "mercado_pago_webhook_events", ["payment_order_id"])


def downgrade() -> None:
    op.drop_index("ix_mercado_pago_webhook_payment_order", table_name="mercado_pago_webhook_events")
    op.drop_index("ix_mercado_pago_webhook_resource", table_name="mercado_pago_webhook_events")
    op.drop_table("mercado_pago_webhook_events")
    postgresql.ENUM(name="mercado_pago_webhook_processing_status").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_payment_orders_external_payment", table_name="payment_orders")
    op.drop_index("ix_payment_orders_external_preference", table_name="payment_orders")
    op.drop_column("payment_orders", "last_provider_sync_at")
    op.drop_column("payment_orders", "provider_status_detail")
    op.drop_column("payment_orders", "provider_status")
    op.drop_column("payment_orders", "sandbox_checkout_url")
    op.drop_column("payment_orders", "checkout_url")
    op.drop_column("payment_orders", "external_preference_id")
