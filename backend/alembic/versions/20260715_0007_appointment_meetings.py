"""connect external meetings to appointments"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0007"
down_revision = "20260715_0006"
branch_labels = None
depends_on = None


appointment_meeting_status = postgresql.ENUM(
    "pending",
    "provisioning",
    "ready",
    "failed",
    "fallback_ready",
    "cancelled",
    "not_required",
    name="appointment_meeting_status",
)
appointment_meeting_status_existing = postgresql.ENUM(
    "pending",
    "provisioning",
    "ready",
    "failed",
    "fallback_ready",
    "cancelled",
    "not_required",
    name="appointment_meeting_status",
    create_type=False,
)


def upgrade() -> None:
    appointment_meeting_status.create(op.get_bind(), checkfirst=True)
    op.add_column("external_meetings", sa.Column("appointment_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_external_meetings_appointment_id", "external_meetings", "appointments", ["appointment_id"], ["id"])
    op.create_index("ix_external_meetings_appointment_id", "external_meetings", ["appointment_id"])
    op.create_table(
        "appointment_meetings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            postgresql.ENUM("mock", "google_meet", "zoom", "manual", name="meeting_provider", create_type=False),
            nullable=True,
        ),
        sa.Column("status", appointment_meeting_status_existing, server_default="pending", nullable=False),
        sa.Column("meeting_url", sa.String(length=500), nullable=True),
        sa.Column("external_meeting_id", sa.Integer(), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("calendar_event_id", sa.String(length=255), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("fallback_reason", sa.String(length=120), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("attempt", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["external_meeting_id"], ["external_meetings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appointment_id", name="uq_appointment_meetings_appointment"),
    )
    op.create_index("ix_appointment_meetings_status", "appointment_meetings", ["status"])
    op.create_index("ix_appointment_meetings_provider", "appointment_meetings", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_appointment_meetings_provider", table_name="appointment_meetings")
    op.drop_index("ix_appointment_meetings_status", table_name="appointment_meetings")
    op.drop_table("appointment_meetings")
    op.drop_index("ix_external_meetings_appointment_id", table_name="external_meetings")
    op.drop_constraint("fk_external_meetings_appointment_id", "external_meetings", type_="foreignkey")
    op.drop_column("external_meetings", "appointment_id")
    appointment_meeting_status.drop(op.get_bind(), checkfirst=True)
