"""add google sheets exports

Revision ID: 20260717_0018
Revises: 20260717_0017
Create Date: 2026-07-17 00:18:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260717_0018"
down_revision: str | None = "20260717_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    export_mode = postgresql.ENUM("upsert", "append_only", name="google_sheets_export_mode", create_type=False)
    execution_status = postgresql.ENUM("pending", "running", "succeeded", "partially_succeeded", "failed", name="google_sheets_export_execution_status", create_type=False)
    export_mode.create(op.get_bind(), checkfirst=True)
    execution_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "google_sheets_export_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("spreadsheet_id", sa.String(length=220), nullable=False),
        sa.Column("sheet_name", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("export_mode", export_mode, server_default="upsert", nullable=False),
        sa.Column("date_range_mode", sa.String(length=40), server_default="custom", nullable=False),
        sa.Column("include_cancelled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_exported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "spreadsheet_id", "sheet_name", name="uq_google_sheets_export_destination"),
    )
    op.create_index("ix_google_sheets_export_configs_integration", "google_sheets_export_configs", ["integration_id"])
    op.create_table(
        "google_sheets_export_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column("status", execution_status, server_default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("range_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("include_cancelled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("total_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("inserted_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["config_id"], ["google_sheets_export_configs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_google_sheets_export_executions_config", "google_sheets_export_executions", ["config_id"])
    op.create_index("ix_google_sheets_export_executions_status", "google_sheets_export_executions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_google_sheets_export_executions_status", table_name="google_sheets_export_executions")
    op.drop_index("ix_google_sheets_export_executions_config", table_name="google_sheets_export_executions")
    op.drop_table("google_sheets_export_executions")
    op.drop_index("ix_google_sheets_export_configs_integration", table_name="google_sheets_export_configs")
    op.drop_table("google_sheets_export_configs")
    sa.Enum(name="google_sheets_export_execution_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="google_sheets_export_mode").drop(op.get_bind(), checkfirst=True)
