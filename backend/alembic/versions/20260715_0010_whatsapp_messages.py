"""add whatsapp messages"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0010"
down_revision = "20260715_0009"
branch_labels = None
depends_on = None


whatsapp_message_status = postgresql.ENUM(
    "queued",
    "accepted",
    "sent",
    "delivered",
    "read",
    "failed",
    "cancelled",
    "skipped",
    name="whatsapp_message_status",
)
whatsapp_message_status_existing = postgresql.ENUM(
    "queued",
    "accepted",
    "sent",
    "delivered",
    "read",
    "failed",
    "cancelled",
    "skipped",
    name="whatsapp_message_status",
    create_type=False,
)
whatsapp_template_purpose_existing = postgresql.ENUM(
    "appointment_confirmation",
    "appointment_reminder",
    "appointment_updated",
    "appointment_cancelled",
    "meeting_ready",
    name="whatsapp_template_purpose",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    whatsapp_message_status.create(bind, checkfirst=True)
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("purpose", whatsapp_template_purpose_existing, nullable=False),
        sa.Column("recipient_hash", sa.String(length=64), nullable=False),
        sa.Column("recipient_masked", sa.String(length=40), nullable=False),
        sa.Column("status", whatsapp_message_status_existing, nullable=False),
        sa.Column("external_message_id", sa.String(length=160), nullable=True),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("attempt", sa.Integer(), server_default="1", nullable=False),
        sa.Column("fallback_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["whatsapp_templates.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "idempotency_key", name="uq_whatsapp_messages_integration_idempotency"),
    )
    op.create_index("ix_whatsapp_messages_external_message_id", "whatsapp_messages", ["external_message_id"])
    op.create_index("ix_whatsapp_messages_status_created_at", "whatsapp_messages", ["status", "created_at"])
    op.create_index("ix_whatsapp_messages_integration_created_at", "whatsapp_messages", ["integration_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_whatsapp_messages_integration_created_at", table_name="whatsapp_messages")
    op.drop_index("ix_whatsapp_messages_status_created_at", table_name="whatsapp_messages")
    op.drop_index("ix_whatsapp_messages_external_message_id", table_name="whatsapp_messages")
    op.drop_table("whatsapp_messages")
    bind = op.get_bind()
    whatsapp_message_status.drop(bind, checkfirst=True)
