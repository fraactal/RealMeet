"""add payment booking policies

Revision ID: 20260719_0022
Revises: 20260719_0021
Create Date: 2026-07-19 00:22:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260719_0022"
down_revision: str | None = "20260719_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    timing = postgresql.ENUM("no_payment", "pay_before_confirmation", "pay_after_confirmation", name="payment_timing")
    timing.create(bind, checkfirst=True)

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'pending_payment'")

    timing_ref = postgresql.ENUM(name="payment_timing", create_type=False)
    op.add_column("professional_profiles", sa.Column("payment_timing", timing_ref, server_default="no_payment", nullable=False))
    op.add_column("professional_profiles", sa.Column("payment_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("professional_profiles", sa.Column("payment_currency", sa.String(length=3), server_default="CLP", nullable=False))
    op.add_column("professional_profiles", sa.Column("payment_expiration_minutes", sa.Integer(), server_default="30", nullable=False))
    op.add_column("professional_profiles", sa.Column("allow_manual_confirmation", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.create_check_constraint("ck_professional_payment_amount_positive", "professional_profiles", "payment_amount IS NULL OR payment_amount > 0")
    op.create_check_constraint("ck_professional_payment_clp_integer", "professional_profiles", "payment_currency <> 'CLP' OR payment_amount IS NULL OR payment_amount = trunc(payment_amount)")
    op.create_check_constraint("ck_professional_payment_expiration_range", "professional_profiles", "payment_expiration_minutes BETWEEN 5 AND 1440")
    op.create_check_constraint("ck_professional_payment_currency_clp", "professional_profiles", "payment_currency = 'CLP'")


def downgrade() -> None:
    op.drop_constraint("ck_professional_payment_currency_clp", "professional_profiles", type_="check")
    op.drop_constraint("ck_professional_payment_expiration_range", "professional_profiles", type_="check")
    op.drop_constraint("ck_professional_payment_clp_integer", "professional_profiles", type_="check")
    op.drop_constraint("ck_professional_payment_amount_positive", "professional_profiles", type_="check")
    op.drop_column("professional_profiles", "allow_manual_confirmation")
    op.drop_column("professional_profiles", "payment_expiration_minutes")
    op.drop_column("professional_profiles", "payment_currency")
    op.drop_column("professional_profiles", "payment_amount")
    op.drop_column("professional_profiles", "payment_timing")
    postgresql.ENUM(name="payment_timing").drop(op.get_bind(), checkfirst=True)
