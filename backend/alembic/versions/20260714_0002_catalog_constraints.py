"""add professional catalog constraints"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_0002"
down_revision = "20260611_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    duplicate_count = op.get_bind().execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT professional_id, specialty_id
                FROM professional_specialties
                GROUP BY professional_id, specialty_id
                HAVING COUNT(*) > 1
            ) duplicates
            """
        )
    ).scalar_one()

    if duplicate_count:
        raise RuntimeError("Cannot add uq_professional_specialty_pair while duplicate professional specialties exist")

    op.create_unique_constraint(
        "uq_professional_specialty_pair",
        "professional_specialties",
        ["professional_id", "specialty_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_professional_specialty_pair", "professional_specialties", type_="unique")
