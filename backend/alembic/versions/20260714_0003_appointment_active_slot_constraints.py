"""add active appointment slot constraints"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_0003"
down_revision = "20260714_0002"
branch_labels = None
depends_on = None


ACTIVE_STATUSES = "'pending', 'confirmed'"


def upgrade() -> None:
    bind = op.get_bind()
    professional_duplicates = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT professional_id, start_datetime, end_datetime
                FROM appointments
                WHERE status IN ('pending', 'confirmed')
                GROUP BY professional_id, start_datetime, end_datetime
                HAVING COUNT(*) > 1
            ) duplicates
            """
        )
    ).scalar_one()
    if professional_duplicates:
        raise RuntimeError("Cannot add active professional slot index while duplicate active appointments exist")

    client_duplicates = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT client_id, start_datetime, end_datetime
                FROM appointments
                WHERE status IN ('pending', 'confirmed')
                GROUP BY client_id, start_datetime, end_datetime
                HAVING COUNT(*) > 1
            ) duplicates
            """
        )
    ).scalar_one()
    if client_duplicates:
        raise RuntimeError("Cannot add active client slot index while duplicate active appointments exist")

    op.create_index(
        "uq_appointments_active_professional_slot",
        "appointments",
        ["professional_id", "start_datetime", "end_datetime"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'confirmed')"),
    )
    op.create_index(
        "uq_appointments_active_client_slot",
        "appointments",
        ["client_id", "start_datetime", "end_datetime"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'confirmed')"),
    )


def downgrade() -> None:
    op.drop_index("uq_appointments_active_client_slot", table_name="appointments")
    op.drop_index("uq_appointments_active_professional_slot", table_name="appointments")
