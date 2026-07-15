"""appointment notifications

Revision ID: 20260715_0011
Revises: 20260715_0010
Create Date: 2026-07-15 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260715_0011"
down_revision: str | None = "20260715_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


event_enum = postgresql.ENUM(
    "appointment_confirmed",
    "appointment_updated",
    "appointment_cancelled",
    "appointment_reminder",
    "meeting_ready",
    name="appointment_notification_event",
    create_type=False,
)
channel_enum = postgresql.ENUM("email", "whatsapp", name="appointment_notification_channel", create_type=False)
status_enum = postgresql.ENUM(
    "pending",
    "processing",
    "accepted",
    "sent",
    "delivered",
    "read",
    "failed",
    "skipped",
    "cancelled",
    "fallback_sent",
    name="appointment_notification_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE appointment_notification_event AS ENUM "
        "('appointment_confirmed', 'appointment_updated', 'appointment_cancelled', 'appointment_reminder', 'meeting_ready'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.execute("DO $$ BEGIN CREATE TYPE appointment_notification_channel AS ENUM ('email', 'whatsapp'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute(
        "DO $$ BEGIN CREATE TYPE appointment_notification_status AS ENUM "
        "('pending', 'processing', 'accepted', 'sent', 'delivered', 'read', 'failed', 'skipped', 'cancelled', 'fallback_sent'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.create_table(
        "appointment_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", event_enum, nullable=False),
        sa.Column("channel", channel_enum, nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("whatsapp_message_id", sa.Integer(), nullable=True),
        sa.Column("email_reference", sa.String(length=180), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("recipient_masked", sa.String(length=80), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("idempotency_key", sa.String(length=220), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["whatsapp_templates.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["whatsapp_message_id"], ["whatsapp_messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_appointment_notifications_idempotency_key"),
    )
    op.create_index("ix_appointment_notifications_appointment_event", "appointment_notifications", ["appointment_id", "event_type"])
    op.create_index("ix_appointment_notifications_status_scheduled", "appointment_notifications", ["status", "scheduled_for"])
    op.create_index("ix_appointment_notifications_whatsapp_message", "appointment_notifications", ["whatsapp_message_id"])


def downgrade() -> None:
    op.drop_index("ix_appointment_notifications_whatsapp_message", table_name="appointment_notifications")
    op.drop_index("ix_appointment_notifications_status_scheduled", table_name="appointment_notifications")
    op.drop_index("ix_appointment_notifications_appointment_event", table_name="appointment_notifications")
    op.drop_table("appointment_notifications")
    op.execute("DROP TYPE IF EXISTS appointment_notification_status")
    op.execute("DROP TYPE IF EXISTS appointment_notification_channel")
    op.execute("DROP TYPE IF EXISTS appointment_notification_event")
