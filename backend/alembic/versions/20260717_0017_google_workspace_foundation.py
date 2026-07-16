"""add google workspace foundation

Revision ID: 20260717_0017
Revises: 20260716_0016
Create Date: 2026-07-17 00:17:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260717_0017"
down_revision: str | None = "20260716_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "integration_oauth_states",
        sa.Column("requested_services", postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.create_table(
        "google_workspace_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("calendar_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("meet_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sheets_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("drive_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("docs_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("calendar_authorized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("meet_authorized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sheets_authorized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("drive_authorized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("docs_authorized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_calendar_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_meet_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sheets_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_drive_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_docs_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_service", sa.String(length=40), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", name="uq_google_workspace_settings_integration"),
    )


def downgrade() -> None:
    op.drop_table("google_workspace_settings")
    op.drop_column("integration_oauth_states", "requested_services")
