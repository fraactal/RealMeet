"""add outbound webhook subscriptions and deliveries

Revision ID: 20260715_0012
Revises: 20260715_0011
Create Date: 2026-07-15 23:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260715_0012"
down_revision: str | None = "20260715_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


delivery_status = postgresql.ENUM("pending", "sending", "succeeded", "failed", "skipped", name="webhook_delivery_status")
delivery_status_existing = postgresql.ENUM("pending", "sending", "succeeded", "failed", "skipped", name="webhook_delivery_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    delivery_status.create(bind, checkfirst=True)
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("target_url", sa.String(length=500), nullable=False),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column("secret_reference", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_subscriptions_integration_id", "webhook_subscriptions", ["integration_id"])
    op.create_index("ix_webhook_subscriptions_enabled", "webhook_subscriptions", ["enabled"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("status", delivery_status_existing, server_default="pending", nullable=False),
        sa.Column("attempt", sa.Integer(), server_default="1", nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["webhook_subscriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subscription_id", "event_id", name="uq_webhook_deliveries_subscription_event"),
    )
    op.create_index("ix_webhook_deliveries_subscription_created", "webhook_deliveries", ["subscription_id", "created_at"])
    op.create_index("ix_webhook_deliveries_status_created", "webhook_deliveries", ["status", "created_at"])
    op.create_index("ix_webhook_deliveries_event_type", "webhook_deliveries", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_event_type", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_status_created", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_subscription_created", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhook_subscriptions_enabled", table_name="webhook_subscriptions")
    op.drop_index("ix_webhook_subscriptions_integration_id", table_name="webhook_subscriptions")
    op.drop_table("webhook_subscriptions")
    bind = op.get_bind()
    delivery_status.drop(bind, checkfirst=True)
