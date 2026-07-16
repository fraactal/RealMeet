"""add external calendars

Revision ID: 20260716_0014
Revises: 20260715_0013
Create Date: 2026-07-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0014"
down_revision: str | None = "20260715_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


external_calendar_provider = postgresql.ENUM("fake", "google_calendar", "microsoft_365", name="external_calendar_provider", create_type=False)
external_calendar_sync_status = postgresql.ENUM("pending", "active", "disabled", "error", name="external_calendar_sync_status", create_type=False)
calendar_conflict_policy = postgresql.ENUM("internal_only", "external_busy_blocks", "disabled", name="calendar_conflict_policy", create_type=False)


def upgrade() -> None:
    external_calendar_provider.create(op.get_bind(), checkfirst=True)
    external_calendar_sync_status.create(op.get_bind(), checkfirst=True)
    calendar_conflict_policy.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "external_calendars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=True),
        sa.Column("provider", external_calendar_provider, nullable=False),
        sa.Column("external_calendar_id", sa.String(length=180), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("read_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("write_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("conflict_check_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sync_status", external_calendar_sync_status, nullable=False, server_default="pending"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["professional_id"], ["professional_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("professional_id", "provider", "external_calendar_id", name="uq_external_calendar_professional_provider_external"),
    )
    op.create_index("ix_external_calendars_professional_id", "external_calendars", ["professional_id"])
    op.create_index("ix_external_calendars_integration_id", "external_calendars", ["integration_id"])
    op.create_index("ix_external_calendars_enabled", "external_calendars", ["enabled"])
    op.create_index(
        "uq_external_calendar_primary_professional_provider",
        "external_calendars",
        ["professional_id", "provider"],
        unique=True,
        postgresql_where=sa.text("is_primary = true"),
    )

    op.create_table(
        "calendar_sync_settings",
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("sync_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("conflict_policy", calendar_conflict_policy, nullable=False, server_default="internal_only"),
        sa.Column("lookback_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lookahead_days", sa.Integer(), server_default="90", nullable=False),
        sa.Column("default_external_calendar_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["default_external_calendar_id"], ["external_calendars.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["professional_id"], ["professional_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("professional_id"),
    )


def downgrade() -> None:
    op.drop_table("calendar_sync_settings")
    op.drop_index("uq_external_calendar_primary_professional_provider", table_name="external_calendars", postgresql_where=sa.text("is_primary = true"))
    op.drop_index("ix_external_calendars_enabled", table_name="external_calendars")
    op.drop_index("ix_external_calendars_integration_id", table_name="external_calendars")
    op.drop_index("ix_external_calendars_professional_id", table_name="external_calendars")
    op.drop_table("external_calendars")
    calendar_conflict_policy.drop(op.get_bind(), checkfirst=True)
    external_calendar_sync_status.drop(op.get_bind(), checkfirst=True)
    external_calendar_provider.drop(op.get_bind(), checkfirst=True)
