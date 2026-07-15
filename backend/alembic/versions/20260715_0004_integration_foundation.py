"""add integration domain persistence"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0004"
down_revision = "20260714_0003"
branch_labels = None
depends_on = None


integration_type = postgresql.ENUM("meeting", "calendar", "messaging", "email", "automation", "webhook", name="integration_type")
integration_provider = postgresql.ENUM(
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
)
integration_status = postgresql.ENUM("not_configured", "configured", "healthy", "error", "unsupported", name="integration_status")
integration_execution_status = postgresql.ENUM("pending", "running", "succeeded", "failed", "skipped", name="integration_execution_status")


def upgrade() -> None:
    integration_type.create(op.get_bind(), checkfirst=True)
    integration_provider.create(op.get_bind(), checkfirst=True)
    integration_status.create(op.get_bind(), checkfirst=True)
    integration_execution_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "integration_type",
            postgresql.ENUM("meeting", "calendar", "messaging", "email", "automation", "webhook", name="integration_type", create_type=False),
            nullable=False,
        ),
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
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("not_configured", "configured", "healthy", "error", "unsupported", name="integration_status", create_type=False),
            server_default="not_configured",
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column("secret_reference", sa.String(length=128), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integrations_enabled", "integrations", ["enabled"])
    op.create_index("ix_integrations_provider", "integrations", ["provider"])
    op.create_index("ix_integrations_status", "integrations", ["status"])
    op.create_index("ix_integrations_type", "integrations", ["integration_type"])

    op.create_table(
        "integration_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=120), nullable=True),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "running", "succeeded", "failed", "skipped", name="integration_execution_status", create_type=False),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("attempt", sa.Integer(), server_default="1", nullable=False),
        sa.Column("request_metadata", sa.JSON(), nullable=True),
        sa.Column("response_metadata", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "idempotency_key", name="uq_integration_executions_integration_idempotency"),
    )
    op.create_index("ix_integration_executions_created_at", "integration_executions", ["created_at"])
    op.create_index("ix_integration_executions_idempotency_key", "integration_executions", ["idempotency_key"])
    op.create_index("ix_integration_executions_integration_id", "integration_executions", ["integration_id"])
    op.create_index("ix_integration_executions_status", "integration_executions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_integration_executions_status", table_name="integration_executions")
    op.drop_index("ix_integration_executions_integration_id", table_name="integration_executions")
    op.drop_index("ix_integration_executions_idempotency_key", table_name="integration_executions")
    op.drop_index("ix_integration_executions_created_at", table_name="integration_executions")
    op.drop_table("integration_executions")

    op.drop_index("ix_integrations_type", table_name="integrations")
    op.drop_index("ix_integrations_status", table_name="integrations")
    op.drop_index("ix_integrations_provider", table_name="integrations")
    op.drop_index("ix_integrations_enabled", table_name="integrations")
    op.drop_table("integrations")

    integration_execution_status.drop(op.get_bind(), checkfirst=True)
    integration_status.drop(op.get_bind(), checkfirst=True)
    integration_provider.drop(op.get_bind(), checkfirst=True)
    integration_type.drop(op.get_bind(), checkfirst=True)
