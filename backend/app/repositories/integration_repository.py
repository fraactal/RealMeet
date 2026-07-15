from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
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

    def list_filtered(
        self,
        *,
        integration_type: IntegrationType | None = None,
        provider: IntegrationProvider | None = None,
        enabled: bool | None = None,
        status: IntegrationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Integration]:
        query = self._filtered_query(integration_type=integration_type, provider=provider, enabled=enabled, status=status)
        return self.db.scalars(query.order_by(Integration.created_at.desc(), Integration.id.desc()).offset(offset).limit(limit)).all()

    def count_filtered(
        self,
        *,
        integration_type: IntegrationType | None = None,
        provider: IntegrationProvider | None = None,
        enabled: bool | None = None,
        status: IntegrationStatus | None = None,
    ) -> int:
        query = select(func.count(Integration.id))
        conditions = self._conditions(integration_type=integration_type, provider=provider, enabled=enabled, status=status)
        if conditions:
            query = query.where(*conditions)
        return self.db.scalar(query) or 0

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

    @staticmethod
    def _conditions(
        *,
        integration_type: IntegrationType | None,
        provider: IntegrationProvider | None,
        enabled: bool | None,
        status: IntegrationStatus | None,
    ) -> list:
        conditions = []
        if integration_type is not None:
            conditions.append(Integration.integration_type == integration_type)
        if provider is not None:
            conditions.append(Integration.provider == provider)
        if enabled is not None:
            conditions.append(Integration.enabled.is_(enabled))
        if status is not None:
            conditions.append(Integration.status == status)
        return conditions

    def _filtered_query(
        self,
        *,
        integration_type: IntegrationType | None,
        provider: IntegrationProvider | None,
        enabled: bool | None,
        status: IntegrationStatus | None,
    ):
        query = select(Integration)
        conditions = self._conditions(integration_type=integration_type, provider=provider, enabled=enabled, status=status)
        if conditions:
            query = query.where(*conditions)
        return query
