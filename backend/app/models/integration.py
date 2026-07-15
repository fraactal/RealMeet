from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType
from app.models.mixins import TimestampMixin


class Integration(Base, TimestampMixin):
    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    integration_type: Mapped[IntegrationType] = mapped_column(Enum(IntegrationType, name="integration_type"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider, name="integration_provider"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus, name="integration_status"),
        default=IntegrationStatus.not_configured,
        nullable=False,
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    secret_reference: Mapped[str | None] = mapped_column(String(128))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(String(500))

    executions: Mapped[list["IntegrationExecution"]] = relationship("IntegrationExecution", back_populates="integration")


class IntegrationExecution(Base):
    __tablename__ = "integration_executions"
    __table_args__ = (UniqueConstraint("integration_id", "idempotency_key", name="uq_integration_executions_integration_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id"), nullable=False)
    operation: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(120))
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[IntegrationExecutionStatus] = mapped_column(
        Enum(IntegrationExecutionStatus, name="integration_execution_status"),
        default=IntegrationExecutionStatus.pending,
        nullable=False,
    )
    attempt: Mapped[int] = mapped_column(default=1, nullable=False)
    request_metadata: Mapped[dict | None] = mapped_column(JSON)
    response_metadata: Mapped[dict | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    integration: Mapped[Integration] = relationship("Integration", back_populates="executions")
