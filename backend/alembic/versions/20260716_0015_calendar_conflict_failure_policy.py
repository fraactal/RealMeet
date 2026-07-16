"""add calendar conflict failure policy

Revision ID: 20260716_0015
Revises: 20260716_0014
Create Date: 2026-07-16 00:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260716_0015"
down_revision: str | None = "20260716_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


external_conflict_failure_policy = postgresql.ENUM("fail_closed", "fail_open", name="external_conflict_failure_policy", create_type=False)


def upgrade() -> None:
    external_conflict_failure_policy.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "calendar_sync_settings",
        sa.Column(
            "external_conflict_failure_policy",
            external_conflict_failure_policy,
            server_default="fail_closed",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("calendar_sync_settings", "external_conflict_failure_policy")
    external_conflict_failure_policy.drop(op.get_bind(), checkfirst=True)
