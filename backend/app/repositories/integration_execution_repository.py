from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration import IntegrationExecution
from app.schemas.integrations import IntegrationExecutionCreate


class IntegrationExecutionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: IntegrationExecutionCreate) -> IntegrationExecution:
        execution = IntegrationExecution(**payload.model_dump())
        self.db.add(execution)
        self.db.flush()
        return execution

    def get(self, execution_id: int) -> IntegrationExecution | None:
        return self.db.get(IntegrationExecution, execution_id)

    def get_by_idempotency_key(self, integration_id: int, idempotency_key: str) -> IntegrationExecution | None:
        return self.db.scalar(
            select(IntegrationExecution).where(
                IntegrationExecution.integration_id == integration_id,
                IntegrationExecution.idempotency_key == idempotency_key,
            )
        )

    def list_recent_for_integration(self, integration_id: int, *, limit: int = 20) -> Sequence[IntegrationExecution]:
        return self.db.scalars(
            select(IntegrationExecution)
            .where(IntegrationExecution.integration_id == integration_id)
            .order_by(IntegrationExecution.created_at.desc(), IntegrationExecution.id.desc())
            .limit(limit)
        ).all()
