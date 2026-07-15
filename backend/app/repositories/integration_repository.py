from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationProvider, IntegrationType
from app.models.integration import Integration
from app.schemas.integrations import IntegrationCreate, IntegrationUpdate


class IntegrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: IntegrationCreate) -> Integration:
        integration = Integration(**payload.model_dump())
        self.db.add(integration)
        self.db.flush()
        return integration

    def get(self, integration_id: int) -> Integration | None:
        return self.db.get(Integration, integration_id)

    def list(self) -> Sequence[Integration]:
        return self.db.scalars(select(Integration).order_by(Integration.created_at.desc(), Integration.id.desc())).all()

    def list_by_type(self, integration_type: IntegrationType) -> Sequence[Integration]:
        return self.db.scalars(select(Integration).where(Integration.integration_type == integration_type)).all()

    def list_by_provider(self, provider: IntegrationProvider) -> Sequence[Integration]:
        return self.db.scalars(select(Integration).where(Integration.provider == provider)).all()

    def update_allowed_fields(self, integration: Integration, payload: IntegrationUpdate) -> Integration:
        values = payload.model_dump(exclude_unset=True)
        for field in ("name", "config", "secret_reference"):
            if field in values:
                setattr(integration, field, values[field])
        self.db.flush()
        return integration
