"""add google docs templates

Revision ID: 20260718_0019
Revises: 20260717_0018
Create Date: 2026-07-18 00:19:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260718_0019"
down_revision: str | None = "20260717_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    doc_type = postgresql.ENUM("appointment_summary", "appointment_confirmation", "pre_session_instructions", "post_session_instructions", "administrative_receipt", "custom_operational", name="google_docs_document_type")
    sharing_policy = postgresql.ENUM("private", "professional_only", "professional_and_client", name="google_docs_sharing_policy")
    doc_status = postgresql.ENUM("pending", "generated", "partially_generated", "failed", "reconcile_required", name="appointment_generated_document_status")
    sharing_status = postgresql.ENUM("not_requested", "private", "shared", "partially_shared", "failed", name="appointment_generated_document_sharing_status")
    doc_type.create(op.get_bind(), checkfirst=True)
    sharing_policy.create(op.get_bind(), checkfirst=True)
    doc_status.create(op.get_bind(), checkfirst=True)
    sharing_status.create(op.get_bind(), checkfirst=True)
    doc_type_ref = postgresql.ENUM(name="google_docs_document_type", create_type=False)
    sharing_policy_ref = postgresql.ENUM(name="google_docs_sharing_policy", create_type=False)
    doc_status_ref = postgresql.ENUM(name="appointment_generated_document_status", create_type=False)
    sharing_status_ref = postgresql.ENUM(name="appointment_generated_document_sharing_status", create_type=False)
    op.create_table(
        "google_docs_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("document_type", doc_type_ref, nullable=False),
        sa.Column("source_document_id", sa.String(length=220), nullable=False),
        sa.Column("destination_folder_id", sa.String(length=220), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("allowed_variables", postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'[]'::json"), nullable=False),
        sa.Column("sharing_policy", sharing_policy_ref, server_default="private", nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_validation_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_validation_error_code", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "source_document_id", name="uq_google_docs_template_source"),
    )
    op.create_index("ix_google_docs_templates_integration", "google_docs_templates", ["integration_id"])
    op.create_table(
        "appointment_generated_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("provider", postgresql.ENUM(name="integration_provider", create_type=False), nullable=False),
        sa.Column("external_document_id", sa.String(length=220), nullable=True),
        sa.Column("external_file_id", sa.String(length=220), nullable=True),
        sa.Column("document_name", sa.String(length=240), nullable=False),
        sa.Column("status", doc_status_ref, server_default="pending", nullable=False),
        sa.Column("sharing_status", sharing_status_ref, server_default="not_requested", nullable=False),
        sa.Column("sharing_policy", sharing_policy_ref, server_default="private", nullable=False),
        sa.Column("generation_request_id", sa.String(length=180), nullable=False),
        sa.Column("generated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["google_docs_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appointment_id", "template_id", "generation_request_id", name="uq_appointment_generated_document_request"),
    )
    op.create_index("ix_appointment_generated_documents_appointment", "appointment_generated_documents", ["appointment_id"])
    op.create_index("ix_appointment_generated_documents_template", "appointment_generated_documents", ["template_id"])


def downgrade() -> None:
    op.drop_index("ix_appointment_generated_documents_template", table_name="appointment_generated_documents")
    op.drop_index("ix_appointment_generated_documents_appointment", table_name="appointment_generated_documents")
    op.drop_table("appointment_generated_documents")
    op.drop_index("ix_google_docs_templates_integration", table_name="google_docs_templates")
    op.drop_table("google_docs_templates")
    postgresql.ENUM(name="appointment_generated_document_sharing_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="appointment_generated_document_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="google_docs_sharing_policy").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="google_docs_document_type").drop(op.get_bind(), checkfirst=True)
