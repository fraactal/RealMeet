"""add appointment external calendar events

Revision ID: 20260716_0016
Revises: 20260716_0015
Create Date: 2026-07-16 00:16:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0016"
down_revision: str | None = "20260716_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


event_status = postgresql.ENUM("pending", "created", "updated", "cancelled", "failed", "reconcile_required", name="appointment_external_calendar_event_status", create_type=False)
sync_action = postgresql.ENUM("create", "update", "cancel", "none", name="appointment_external_calendar_sync_action", create_type=False)


def upgrade() -> None:
    event_status.create(op.get_bind(), checkfirst=True)
    sync_action.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "appointment_external_calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("external_calendar_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_event_id", sa.String(length=255), nullable=True),
        sa.Column("status", event_status, server_default="pending", nullable=False),
        sa.Column("sync_action", sync_action, server_default="create", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["external_calendar_id"], ["external_calendars.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appointment_id", "external_calendar_id", name="uq_appointment_external_calendar_event"),
    )
    op.create_index("ix_appointment_external_calendar_events_appointment", "appointment_external_calendar_events", ["appointment_id"])
    op.create_index("ix_appointment_external_calendar_events_status", "appointment_external_calendar_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_appointment_external_calendar_events_status", table_name="appointment_external_calendar_events")
    op.drop_index("ix_appointment_external_calendar_events_appointment", table_name="appointment_external_calendar_events")
    op.drop_table("appointment_external_calendar_events")
    sync_action.drop(op.get_bind(), checkfirst=True)
    event_status.drop(op.get_bind(), checkfirst=True)
