"""add whatsapp webhook events"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0009"
down_revision = "20260715_0008"
branch_labels = None
depends_on = None


whatsapp_webhook_event_type = postgresql.ENUM(
    "inbound_message",
    "message_sent",
    "message_delivered",
    "message_read",
    "message_failed",
    "template_status",
    "unknown",
    name="whatsapp_webhook_event_type",
)
whatsapp_webhook_processing_status = postgresql.ENUM(
    "received",
    "classified",
    "ignored",
    "duplicate",
    "failed",
    name="whatsapp_webhook_processing_status",
)
whatsapp_webhook_event_type_existing = postgresql.ENUM(
    "inbound_message",
    "message_sent",
    "message_delivered",
    "message_read",
    "message_failed",
    "template_status",
    "unknown",
    name="whatsapp_webhook_event_type",
    create_type=False,
)
whatsapp_webhook_processing_status_existing = postgresql.ENUM(
    "received",
    "classified",
    "ignored",
    "duplicate",
    "failed",
    name="whatsapp_webhook_processing_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    whatsapp_webhook_event_type.create(bind, checkfirst=True)
    whatsapp_webhook_processing_status.create(bind, checkfirst=True)
    op.create_table(
        "whatsapp_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=True),
        sa.Column("event_key", sa.String(length=180), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("object_type", sa.String(length=80), nullable=True),
        sa.Column("field", sa.String(length=80), nullable=True),
        sa.Column("event_type", whatsapp_webhook_event_type_existing, nullable=False),
        sa.Column("external_message_id", sa.String(length=160), nullable=True),
        sa.Column("phone_number_id_masked", sa.String(length=40), nullable=True),
        sa.Column("phone_number_id_hash", sa.String(length=64), nullable=True),
        sa.Column("sender_phone_hash", sa.String(length=64), nullable=True),
        sa.Column("recipient_phone_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_status", whatsapp_webhook_processing_status_existing, nullable=False),
        sa.Column("signature_valid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("duplicate", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("received_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("safe_metadata", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key", name="uq_whatsapp_webhook_events_event_key"),
    )
    op.create_index("ix_whatsapp_webhook_events_integration_id", "whatsapp_webhook_events", ["integration_id"])
    op.create_index("ix_whatsapp_webhook_events_event_type", "whatsapp_webhook_events", ["event_type"])
    op.create_index("ix_whatsapp_webhook_events_processing_status", "whatsapp_webhook_events", ["processing_status"])
    op.create_index("ix_whatsapp_webhook_events_received_at", "whatsapp_webhook_events", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_whatsapp_webhook_events_received_at", table_name="whatsapp_webhook_events")
    op.drop_index("ix_whatsapp_webhook_events_processing_status", table_name="whatsapp_webhook_events")
    op.drop_index("ix_whatsapp_webhook_events_event_type", table_name="whatsapp_webhook_events")
    op.drop_index("ix_whatsapp_webhook_events_integration_id", table_name="whatsapp_webhook_events")
    op.drop_table("whatsapp_webhook_events")
    bind = op.get_bind()
    whatsapp_webhook_processing_status.drop(bind, checkfirst=True)
    whatsapp_webhook_event_type.drop(bind, checkfirst=True)
