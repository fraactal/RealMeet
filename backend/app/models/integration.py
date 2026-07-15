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
    credentials: Mapped[list["IntegrationCredential"]] = relationship("IntegrationCredential", back_populates="integration")
    oauth_states: Mapped[list["IntegrationOAuthState"]] = relationship("IntegrationOAuthState", back_populates="integration")
    external_meetings: Mapped[list["ExternalMeeting"]] = relationship("ExternalMeeting", back_populates="integration")


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


class IntegrationCredential(Base, TimestampMixin):
    __tablename__ = "integration_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id"), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(40), nullable=False)
    encrypted_access_token: Mapped[str | None] = mapped_column(Text)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text)
    token_type: Mapped[str | None] = mapped_column(String(40))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    external_account_id: Mapped[str | None] = mapped_column(String(120))
    external_account_email: Mapped[str | None] = mapped_column(String(255))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_refresh_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(String(500))

    integration: Mapped[Integration] = relationship("Integration", back_populates="credentials")


class IntegrationOAuthState(Base):
    __tablename__ = "integration_oauth_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id"), nullable=False)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider, name="integration_provider"), nullable=False)
    nonce_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    integration: Mapped[Integration] = relationship("Integration", back_populates="oauth_states")


class ExternalMeeting(Base, TimestampMixin):
    __tablename__ = "external_meetings"
    __table_args__ = (UniqueConstraint("integration_id", "provider", "external_event_id", name="uq_external_meetings_integration_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider, name="integration_provider"), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    conference_id: Mapped[str | None] = mapped_column(String(120))
    meeting_url: Mapped[str | None] = mapped_column(String(500))
    html_link: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(120))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    integration: Mapped[Integration] = relationship("Integration", back_populates="external_meetings")
