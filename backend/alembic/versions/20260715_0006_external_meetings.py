"""add external meeting references"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0006"
down_revision = "20260715_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_meetings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            postgresql.ENUM(
                "mock",
                "google_meet",
                "google_calendar",
                "microsoft_365",
                "whatsapp_cloud",
                "twilio",
                "smtp",
                "n8n",
                "generic_webhook",
                name="integration_provider",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("external_event_id", sa.String(length=255), nullable=False),
        sa.Column("external_calendar_id", sa.String(length=255), nullable=False),
        sa.Column("conference_id", sa.String(length=120), nullable=True),
        sa.Column("meeting_url", sa.String(length=500), nullable=True),
        sa.Column("html_link", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=120), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "provider", "external_event_id", name="uq_external_meetings_integration_event"),
    )
    op.create_index("ix_external_meetings_integration_id", "external_meetings", ["integration_id"])
    op.create_index("ix_external_meetings_provider", "external_meetings", ["provider"])
    op.create_index("ix_external_meetings_status", "external_meetings", ["status"])


def downgrade() -> None:
    op.drop_index("ix_external_meetings_status", table_name="external_meetings")
    op.drop_index("ix_external_meetings_provider", table_name="external_meetings")
    op.drop_index("ix_external_meetings_integration_id", table_name="external_meetings")
    op.drop_table("external_meetings")
