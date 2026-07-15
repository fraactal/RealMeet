"""add google oauth credential persistence"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260715_0005"
down_revision = "20260715_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("credential_type", sa.String(length=40), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=True),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=40), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
        sa.Column("external_account_id", sa.String(length=120), nullable=True),
        sa.Column("external_account_email", sa.String(length=255), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_refresh_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integration_credentials_integration_id", "integration_credentials", ["integration_id"])
    op.create_index("ix_integration_credentials_type", "integration_credentials", ["credential_type"])
    op.create_index(
        "uq_integration_credentials_active_google",
        "integration_credentials",
        ["integration_id", "credential_type"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "integration_oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
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
        sa.Column("nonce_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nonce_hash", name="uq_integration_oauth_states_nonce_hash"),
    )
    op.create_index("ix_integration_oauth_states_expires_at", "integration_oauth_states", ["expires_at"])
    op.create_index("ix_integration_oauth_states_integration_id", "integration_oauth_states", ["integration_id"])


def downgrade() -> None:
    op.drop_index("ix_integration_oauth_states_integration_id", table_name="integration_oauth_states")
    op.drop_index("ix_integration_oauth_states_expires_at", table_name="integration_oauth_states")
    op.drop_table("integration_oauth_states")

    op.drop_index("uq_integration_credentials_active_google", table_name="integration_credentials")
    op.drop_index("ix_integration_credentials_type", table_name="integration_credentials")
    op.drop_index("ix_integration_credentials_integration_id", table_name="integration_credentials")
    op.drop_table("integration_credentials")
