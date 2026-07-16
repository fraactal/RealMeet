"""add document automation

Revision ID: 20260718_0020
Revises: 20260718_0019
Create Date: 2026-07-18 00:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260718_0020"
down_revision: str | None = "20260718_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    event_type = postgresql.ENUM("appointment.created", "appointment.confirmed", "appointment.cancelled", "meeting.ready", name="document_automation_event_type")
    execution_status = postgresql.ENUM("pending", "running", "succeeded", "partially_succeeded", "failed", "reconcile_required", name="document_automation_execution_status")
    email_status = postgresql.ENUM("not_requested", "sent", "failed", "skipped", name="document_automation_email_status")
    n8n_status = postgresql.ENUM("not_requested", "delivered", "failed", "skipped", name="document_automation_n8n_status")
    email_policy = postgresql.ENUM("none", "professional", "client", "professional_and_client", name="document_automation_email_recipient_policy")
    for enum_type in (event_type, execution_status, email_status, n8n_status, email_policy):
        enum_type.create(op.get_bind(), checkfirst=True)

    event_type_ref = postgresql.ENUM(name="document_automation_event_type", create_type=False)
    sharing_policy_ref = postgresql.ENUM(name="google_docs_sharing_policy", create_type=False)
    execution_status_ref = postgresql.ENUM(name="document_automation_execution_status", create_type=False)
    email_status_ref = postgresql.ENUM(name="document_automation_email_status", create_type=False)
    n8n_status_ref = postgresql.ENUM(name="document_automation_n8n_status", create_type=False)
    email_policy_ref = postgresql.ENUM(name="document_automation_email_recipient_policy", create_type=False)

    op.create_table(
        "google_docs_automation_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("event_type", event_type_ref, nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sharing_policy", sharing_policy_ref, server_default="private", nullable=False),
        sa.Column("email_delivery_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("email_recipient_policy", email_policy_ref, server_default="none", nullable=False),
        sa.Column("n8n_event_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["google_docs_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "template_id", "event_type", "name", name="uq_google_docs_automation_rule_exact"),
    )
    op.create_index("ix_google_docs_automation_rules_integration", "google_docs_automation_rules", ["integration_id"])
    op.create_index("ix_google_docs_automation_rules_template", "google_docs_automation_rules", ["template_id"])
    op.create_index("ix_google_docs_automation_rules_event", "google_docs_automation_rules", ["event_type"])

    op.create_table(
        "document_automation_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("event_type", event_type_ref, nullable=False),
        sa.Column("event_id", sa.String(length=180), nullable=False),
        sa.Column("idempotency_key", sa.String(length=240), nullable=False),
        sa.Column("status", execution_status_ref, server_default="pending", nullable=False),
        sa.Column("generated_document_id", sa.Integer(), nullable=True),
        sa.Column("email_status", email_status_ref, server_default="not_requested", nullable=False),
        sa.Column("n8n_status", n8n_status_ref, server_default="not_requested", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["google_docs_automation_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_document_id"], ["appointment_generated_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_document_automation_execution_idempotency"),
    )
    op.create_index("ix_document_automation_executions_rule", "document_automation_executions", ["rule_id"])
    op.create_index("ix_document_automation_executions_appointment", "document_automation_executions", ["appointment_id"])
    op.create_index("ix_document_automation_executions_status", "document_automation_executions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_document_automation_executions_status", table_name="document_automation_executions")
    op.drop_index("ix_document_automation_executions_appointment", table_name="document_automation_executions")
    op.drop_index("ix_document_automation_executions_rule", table_name="document_automation_executions")
    op.drop_table("document_automation_executions")
    op.drop_index("ix_google_docs_automation_rules_event", table_name="google_docs_automation_rules")
    op.drop_index("ix_google_docs_automation_rules_template", table_name="google_docs_automation_rules")
    op.drop_index("ix_google_docs_automation_rules_integration", table_name="google_docs_automation_rules")
    op.drop_table("google_docs_automation_rules")
    for enum_name in (
        "document_automation_email_recipient_policy",
        "document_automation_n8n_status",
        "document_automation_email_status",
        "document_automation_execution_status",
        "document_automation_event_type",
    ):
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
