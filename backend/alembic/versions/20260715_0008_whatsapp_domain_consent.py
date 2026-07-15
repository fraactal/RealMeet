"""add whatsapp domain consent and templates"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0008"
down_revision = "20260715_0007"
branch_labels = None
depends_on = None


whatsapp_consent_status = postgresql.ENUM("not_granted", "granted", "revoked", name="whatsapp_consent_status")
whatsapp_consent_purpose = postgresql.ENUM(
    "appointment_transactional",
    "appointment_reminders",
    "appointment_updates",
    name="whatsapp_consent_purpose",
)
whatsapp_consent_source = postgresql.ENUM("self_service", "admin_correction", "imported", "system_migration", name="whatsapp_consent_source")
whatsapp_template_status = postgresql.ENUM("draft", "pending", "approved", "rejected", "paused", "disabled", "unknown", name="whatsapp_template_status")
whatsapp_template_category = postgresql.ENUM("utility", "authentication", "marketing", "unknown", name="whatsapp_template_category")
whatsapp_template_purpose = postgresql.ENUM(
    "appointment_confirmation",
    "appointment_reminder",
    "appointment_updated",
    "appointment_cancelled",
    "meeting_ready",
    name="whatsapp_template_purpose",
)
whatsapp_consent_status_existing = postgresql.ENUM("not_granted", "granted", "revoked", name="whatsapp_consent_status", create_type=False)
whatsapp_consent_purpose_existing = postgresql.ENUM(
    "appointment_transactional",
    "appointment_reminders",
    "appointment_updates",
    name="whatsapp_consent_purpose",
    create_type=False,
)
whatsapp_consent_source_existing = postgresql.ENUM("self_service", "admin_correction", "imported", "system_migration", name="whatsapp_consent_source", create_type=False)
whatsapp_template_status_existing = postgresql.ENUM("draft", "pending", "approved", "rejected", "paused", "disabled", "unknown", name="whatsapp_template_status", create_type=False)
whatsapp_template_category_existing = postgresql.ENUM("utility", "authentication", "marketing", "unknown", name="whatsapp_template_category", create_type=False)
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
    whatsapp_consent_status.create(bind, checkfirst=True)
    whatsapp_consent_purpose.create(bind, checkfirst=True)
    whatsapp_consent_source.create(bind, checkfirst=True)
    whatsapp_template_status.create(bind, checkfirst=True)
    whatsapp_template_category.create(bind, checkfirst=True)
    whatsapp_template_purpose.create(bind, checkfirst=True)

    op.create_table(
        "whatsapp_consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone_e164", sa.String(length=20), nullable=False),
        sa.Column("phone_hash", sa.String(length=64), nullable=False),
        sa.Column("phone_masked", sa.String(length=40), nullable=False),
        sa.Column("status", whatsapp_consent_status_existing, server_default="granted", nullable=False),
        sa.Column("purpose", whatsapp_consent_purpose_existing, nullable=False),
        sa.Column("source", whatsapp_consent_source_existing, nullable=False),
        sa.Column("consent_text_version", sa.String(length=40), nullable=False),
        sa.Column("source_reason", sa.String(length=300), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "phone_hash", "purpose", name="uq_whatsapp_consents_user_phone_purpose"),
    )
    op.create_index("ix_whatsapp_consents_phone_hash", "whatsapp_consents", ["phone_hash"])
    op.create_index("ix_whatsapp_consents_user_id", "whatsapp_consents", ["user_id"])
    op.create_index("ix_whatsapp_consents_status", "whatsapp_consents", ["status"])

    op.create_table(
        "whatsapp_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("category", whatsapp_template_category_existing, nullable=False),
        sa.Column("status", whatsapp_template_status_existing, server_default="draft", nullable=False),
        sa.Column("purpose", whatsapp_template_purpose_existing, nullable=False),
        sa.Column("components_schema", sa.JSON(), nullable=False),
        sa.Column("external_template_id", sa.String(length=120), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "name", "language", name="uq_whatsapp_templates_integration_name_language"),
    )
    op.create_index("ix_whatsapp_templates_integration_id", "whatsapp_templates", ["integration_id"])
    op.create_index("ix_whatsapp_templates_status", "whatsapp_templates", ["status"])
    op.create_index("ix_whatsapp_templates_purpose", "whatsapp_templates", ["purpose"])


def downgrade() -> None:
    op.drop_index("ix_whatsapp_templates_purpose", table_name="whatsapp_templates")
    op.drop_index("ix_whatsapp_templates_status", table_name="whatsapp_templates")
    op.drop_index("ix_whatsapp_templates_integration_id", table_name="whatsapp_templates")
    op.drop_table("whatsapp_templates")
    op.drop_index("ix_whatsapp_consents_status", table_name="whatsapp_consents")
    op.drop_index("ix_whatsapp_consents_user_id", table_name="whatsapp_consents")
    op.drop_index("ix_whatsapp_consents_phone_hash", table_name="whatsapp_consents")
    op.drop_table("whatsapp_consents")

    bind = op.get_bind()
    whatsapp_template_purpose.drop(bind, checkfirst=True)
    whatsapp_template_category.drop(bind, checkfirst=True)
    whatsapp_template_status.drop(bind, checkfirst=True)
    whatsapp_consent_source.drop(bind, checkfirst=True)
    whatsapp_consent_purpose.drop(bind, checkfirst=True)
    whatsapp_consent_status.drop(bind, checkfirst=True)
