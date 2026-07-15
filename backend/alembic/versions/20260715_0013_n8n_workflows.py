"""add n8n workflows

Revision ID: 20260715_0013
Revises: 20260715_0012
Create Date: 2026-07-15 23:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260715_0013"
down_revision: str | None = "20260715_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "n8n_workflows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("webhook_path", sa.String(length=240), nullable=False),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("secret_reference", sa.String(length=128), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["webhook_subscriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "webhook_path", name="uq_n8n_workflows_integration_path"),
    )
    op.create_index("ix_n8n_workflows_integration_id", "n8n_workflows", ["integration_id"])
    op.create_index("ix_n8n_workflows_subscription_id", "n8n_workflows", ["subscription_id"])
    op.create_index("ix_n8n_workflows_enabled", "n8n_workflows", ["enabled"])


def downgrade() -> None:
    op.drop_index("ix_n8n_workflows_enabled", table_name="n8n_workflows")
    op.drop_index("ix_n8n_workflows_subscription_id", table_name="n8n_workflows")
    op.drop_index("ix_n8n_workflows_integration_id", table_name="n8n_workflows")
    op.drop_table("n8n_workflows")
