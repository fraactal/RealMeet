from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, selectinload

from app.automation.contracts import DomainEvent
from app.automation.enums import WebhookDeliveryStatus, WebhookEventType
from app.automation.service import WebhookDeliveryService
from app.db.session import Base
from app.emails.service import EmailService, email_service
from app.integrations.enums import IntegrationProvider
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationError, IntegrationProviderExecutionError
from app.integrations.google_workspace.docs_templates import (
    AppointmentGeneratedDocument,
    AppointmentGeneratedDocumentSharingStatus,
    AppointmentGeneratedDocumentStatus,
    GenerateDocumentRequest,
    GoogleDocsSharingPolicy,
    GoogleDocsTemplate,
    GoogleDocsTemplateService,
    ReconcileDocumentRead,
    read_document,
)
from app.models.appointment import Appointment
from app.models.client_profile import ClientProfile
from app.models.integration import Integration
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User, UserRole


class DocumentAutomationEventType(str, enum.Enum):
    appointment_created = "appointment.created"
    appointment_confirmed = "appointment.confirmed"
    appointment_cancelled = "appointment.cancelled"
    meeting_ready = "meeting.ready"


class DocumentAutomationExecutionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    partially_succeeded = "partially_succeeded"
    failed = "failed"
    reconcile_required = "reconcile_required"


class DocumentAutomationEmailStatus(str, enum.Enum):
    not_requested = "not_requested"
    sent = "sent"
    failed = "failed"
    skipped = "skipped"


class DocumentAutomationN8nStatus(str, enum.Enum):
    not_requested = "not_requested"
    delivered = "delivered"
    failed = "failed"
    skipped = "skipped"


class DocumentAutomationEmailRecipientPolicy(str, enum.Enum):
    none = "none"
    professional = "professional"
    client = "client"
    professional_and_client = "professional_and_client"


class DocumentAutomationReconcileResult(str, enum.Enum):
    in_sync = "in_sync"
    document_missing = "document_missing"
    sharing_mismatch = "sharing_mismatch"
    email_pending = "email_pending"
    n8n_pending = "n8n_pending"
    partial = "partial"
    provider_unavailable = "provider_unavailable"


class GoogleDocsAutomationRule(Base):
    __tablename__ = "google_docs_automation_rules"
    __table_args__ = (
        UniqueConstraint("integration_id", "template_id", "event_type", "name", name="uq_google_docs_automation_rule_exact"),
        Index("ix_google_docs_automation_rules_integration", "integration_id"),
        Index("ix_google_docs_automation_rules_template", "template_id"),
        Index("ix_google_docs_automation_rules_event", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[int] = mapped_column(ForeignKey("google_docs_templates.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    event_type: Mapped[DocumentAutomationEventType] = mapped_column(Enum(DocumentAutomationEventType, name="document_automation_event_type", values_callable=lambda items: [item.value for item in items]), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sharing_policy: Mapped[GoogleDocsSharingPolicy] = mapped_column(Enum(GoogleDocsSharingPolicy, name="google_docs_sharing_policy"), default=GoogleDocsSharingPolicy.private, nullable=False)
    email_delivery_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_recipient_policy: Mapped[DocumentAutomationEmailRecipientPolicy] = mapped_column(Enum(DocumentAutomationEmailRecipientPolicy, name="document_automation_email_recipient_policy"), default=DocumentAutomationEmailRecipientPolicy.none, nullable=False)
    n8n_event_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    integration: Mapped[Integration] = relationship("Integration")
    template: Mapped[GoogleDocsTemplate] = relationship("GoogleDocsTemplate")


class DocumentAutomationExecution(Base):
    __tablename__ = "document_automation_executions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_document_automation_execution_idempotency"),
        Index("ix_document_automation_executions_rule", "rule_id"),
        Index("ix_document_automation_executions_appointment", "appointment_id"),
        Index("ix_document_automation_executions_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("google_docs_automation_rules.id", ondelete="CASCADE"), nullable=False)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[DocumentAutomationEventType] = mapped_column(Enum(DocumentAutomationEventType, name="document_automation_event_type", values_callable=lambda items: [item.value for item in items]), nullable=False)
    event_id: Mapped[str] = mapped_column(String(180), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[DocumentAutomationExecutionStatus] = mapped_column(Enum(DocumentAutomationExecutionStatus, name="document_automation_execution_status"), default=DocumentAutomationExecutionStatus.pending, nullable=False)
    generated_document_id: Mapped[int | None] = mapped_column(ForeignKey("appointment_generated_documents.id", ondelete="SET NULL"))
    email_status: Mapped[DocumentAutomationEmailStatus] = mapped_column(Enum(DocumentAutomationEmailStatus, name="document_automation_email_status"), default=DocumentAutomationEmailStatus.not_requested, nullable=False)
    n8n_status: Mapped[DocumentAutomationN8nStatus] = mapped_column(Enum(DocumentAutomationN8nStatus, name="document_automation_n8n_status"), default=DocumentAutomationN8nStatus.not_requested, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(120))
    error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    rule: Mapped[GoogleDocsAutomationRule] = relationship("GoogleDocsAutomationRule")
    appointment: Mapped[Appointment] = relationship("Appointment")
    generated_document: Mapped[AppointmentGeneratedDocument | None] = relationship("AppointmentGeneratedDocument")


class GoogleDocsAutomationRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    event_type: DocumentAutomationEventType
    enabled: bool = False
    sharing_policy: GoogleDocsSharingPolicy = GoogleDocsSharingPolicy.private
    email_delivery_enabled: bool = False
    email_recipient_policy: DocumentAutomationEmailRecipientPolicy = DocumentAutomationEmailRecipientPolicy.none
    n8n_event_enabled: bool = False


class GoogleDocsAutomationRuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    sharing_policy: GoogleDocsSharingPolicy | None = None
    email_delivery_enabled: bool | None = None
    email_recipient_policy: DocumentAutomationEmailRecipientPolicy | None = None
    n8n_event_enabled: bool | None = None


class GoogleDocsAutomationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: int
    template_id: int
    name: str
    description: str | None
    event_type: DocumentAutomationEventType
    enabled: bool
    sharing_policy: GoogleDocsSharingPolicy
    email_delivery_enabled: bool
    email_recipient_policy: DocumentAutomationEmailRecipientPolicy
    n8n_event_enabled: bool
    created_at: datetime
    updated_at: datetime


class DocumentAutomationExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: int
    appointment_id: int
    event_type: DocumentAutomationEventType
    event_id: str
    idempotency_key: str
    status: DocumentAutomationExecutionStatus
    generated_document_id: int | None
    email_status: DocumentAutomationEmailStatus
    n8n_status: DocumentAutomationN8nStatus
    started_at: datetime | None
    finished_at: datetime | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentAutomationTriggerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_id: int
    event_id: str | None = Field(default=None, min_length=3, max_length=120)


class DocumentAutomationReconcileRead(BaseModel):
    result: DocumentAutomationReconcileResult
    execution: DocumentAutomationExecutionRead


def read_automation_execution(item: DocumentAutomationExecution) -> DocumentAutomationExecutionRead:
    return DocumentAutomationExecutionRead.model_validate(item)


def automation_safe_message(code: str) -> str:
    messages = {
        "document_automation_rule_invalid": "La regla documental no es valida.",
        "document_automation_template_disabled": "La plantilla esta deshabilitada.",
        "document_automation_generation_failed": "No pudimos generar el documento.",
        "document_automation_sharing_failed": "No pudimos compartir el documento.",
        "document_automation_email_failed": "No pudimos enviar el email.",
        "document_automation_n8n_failed": "No pudimos notificar el evento documental.",
        "document_automation_reconcile_required": "La ejecucion requiere reconciliacion.",
    }
    return messages.get(code, "No pudimos completar la automatizacion documental.")


class DocumentAutomationService:
    def __init__(
        self,
        db: Session,
        *,
        docs_service: GoogleDocsTemplateService | None = None,
        mailer: EmailService | None = None,
        webhook_service: WebhookDeliveryService | None = None,
    ) -> None:
        self.db = db
        self.docs_service = docs_service or GoogleDocsTemplateService(db)
        self.mailer = mailer or email_service
        self.webhook_service = webhook_service or WebhookDeliveryService(db)

    def list_rules(self, integration_id: int) -> list[GoogleDocsAutomationRule]:
        self._assert_google_integration(integration_id)
        return list(self.db.scalars(select(GoogleDocsAutomationRule).where(GoogleDocsAutomationRule.integration_id == integration_id).order_by(GoogleDocsAutomationRule.created_at.desc())))

    def create_rule(self, integration_id: int, payload: GoogleDocsAutomationRuleCreate) -> GoogleDocsAutomationRule:
        template = self._template(integration_id, payload.template_id, require_enabled=True)
        if payload.email_delivery_enabled and payload.email_recipient_policy == DocumentAutomationEmailRecipientPolicy.none:
            raise IntegrationConfigurationError("Selecciona destinatarios para email", code="document_automation_rule_invalid")
        rule = GoogleDocsAutomationRule(integration_id=integration_id, template_id=template.id, **payload.model_dump(exclude={"template_id"}))
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rule(self, integration_id: int, rule_id: int) -> GoogleDocsAutomationRule:
        self._assert_google_integration(integration_id)
        rule = self.db.get(GoogleDocsAutomationRule, rule_id)
        if not rule or rule.integration_id != integration_id:
            raise IntegrationConfigurationError("Regla documental no encontrada", code="document_automation_rule_invalid")
        return rule

    def update_rule(self, integration_id: int, rule_id: int, payload: GoogleDocsAutomationRuleUpdate) -> GoogleDocsAutomationRule:
        rule = self.get_rule(integration_id, rule_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        if rule.email_delivery_enabled and rule.email_recipient_policy == DocumentAutomationEmailRecipientPolicy.none:
            raise IntegrationConfigurationError("Selecciona destinatarios para email", code="document_automation_rule_invalid")
        rule.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def set_enabled(self, integration_id: int, rule_id: int, enabled: bool) -> GoogleDocsAutomationRule:
        rule = self.get_rule(integration_id, rule_id)
        self._template(integration_id, rule.template_id, require_enabled=True)
        rule.enabled = enabled
        rule.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def list_executions(self, integration_id: int, *, limit: int = 50) -> list[DocumentAutomationExecution]:
        self._assert_google_integration(integration_id)
        return list(
            self.db.scalars(
                select(DocumentAutomationExecution)
                .join(GoogleDocsAutomationRule)
                .where(GoogleDocsAutomationRule.integration_id == integration_id)
                .order_by(DocumentAutomationExecution.created_at.desc())
                .limit(limit)
            )
        )

    def get_execution(self, integration_id: int, execution_id: int) -> DocumentAutomationExecution:
        execution = self.db.scalar(
            select(DocumentAutomationExecution)
            .options(selectinload(DocumentAutomationExecution.rule))
            .join(GoogleDocsAutomationRule)
            .where(DocumentAutomationExecution.id == execution_id, GoogleDocsAutomationRule.integration_id == integration_id)
        )
        if not execution:
            raise IntegrationConfigurationError("Ejecucion documental no encontrada", code="document_automation_execution_not_found")
        return execution

    def handle_appointment_event(self, event_type: DocumentAutomationEventType, appointment: Appointment, *, event_id: str | None = None, actor: User | None = None) -> list[DocumentAutomationExecution]:
        rules = list(
            self.db.scalars(
                select(GoogleDocsAutomationRule)
                .join(GoogleDocsTemplate, GoogleDocsAutomationRule.template_id == GoogleDocsTemplate.id)
                .where(GoogleDocsAutomationRule.event_type == event_type, GoogleDocsAutomationRule.enabled.is_(True), GoogleDocsTemplate.enabled.is_(True))
            )
        )
        executions: list[DocumentAutomationExecution] = []
        event_key = event_id or f"{event_type.value}:appointment:{appointment.id}"
        for rule in rules:
            executions.append(self.run_rule(rule.integration_id, rule.id, appointment.id, event_id=event_key, actor=actor))
        return executions

    def test_rule(self, integration_id: int, rule_id: int, payload: DocumentAutomationTriggerRequest, actor: User) -> DocumentAutomationExecution:
        event_id = payload.event_id or f"manual:{rule_id}:appointment:{payload.appointment_id}"
        return self.run_rule(integration_id, rule_id, payload.appointment_id, event_id=event_id, actor=actor, force=True)

    def run_rule(self, integration_id: int, rule_id: int, appointment_id: int, *, event_id: str, actor: User | None = None, force: bool = False) -> DocumentAutomationExecution:
        rule = self.get_rule(integration_id, rule_id)
        if not rule.enabled and not force:
            raise IntegrationConfigurationError("La regla documental esta deshabilitada", code="document_automation_rule_invalid")
        appointment = self._appointment(appointment_id)
        key = f"{rule.id}:{appointment.id}:{rule.event_type.value}:{event_id}"
        existing = self.db.scalar(select(DocumentAutomationExecution).where(DocumentAutomationExecution.idempotency_key == key))
        if existing:
            return existing
        execution = DocumentAutomationExecution(
            rule_id=rule.id,
            appointment_id=appointment.id,
            event_type=rule.event_type,
            event_id=event_id,
            idempotency_key=key,
            status=DocumentAutomationExecutionStatus.pending,
            email_status=DocumentAutomationEmailStatus.not_requested if not rule.email_delivery_enabled else DocumentAutomationEmailStatus.skipped,
            n8n_status=DocumentAutomationN8nStatus.not_requested if not rule.n8n_event_enabled else DocumentAutomationN8nStatus.skipped,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return self._execute(execution, actor=actor)

    def retry_execution(self, integration_id: int, execution_id: int, actor: User) -> DocumentAutomationExecution:
        execution = self.get_execution(integration_id, execution_id)
        if execution.status not in {
            DocumentAutomationExecutionStatus.failed,
            DocumentAutomationExecutionStatus.partially_succeeded,
            DocumentAutomationExecutionStatus.reconcile_required,
        }:
            raise IntegrationConfigurationError("La ejecucion no admite retry", code="document_automation_rule_invalid")
        return self._execute(execution, actor=actor)

    def reconcile_execution(self, integration_id: int, execution_id: int) -> DocumentAutomationReconcileRead:
        execution = self.get_execution(integration_id, execution_id)
        if not execution.generated_document_id:
            execution.status = DocumentAutomationExecutionStatus.reconcile_required
            execution.error_code = "document_automation_reconcile_required"
            execution.error_message = automation_safe_message(execution.error_code)
            self.db.commit()
            return DocumentAutomationReconcileRead(result=DocumentAutomationReconcileResult.document_missing, execution=read_automation_execution(execution))
        try:
            result = self.docs_service.reconcile(execution.appointment_id, execution.generated_document_id)
            document = result.document
        except IntegrationError:
            execution.status = DocumentAutomationExecutionStatus.reconcile_required
            execution.error_code = "document_automation_reconcile_required"
            execution.error_message = automation_safe_message(execution.error_code)
            self.db.commit()
            return DocumentAutomationReconcileRead(result=DocumentAutomationReconcileResult.provider_unavailable, execution=read_automation_execution(execution))
        if document.status in {AppointmentGeneratedDocumentStatus.failed, AppointmentGeneratedDocumentStatus.reconcile_required}:
            execution.status = DocumentAutomationExecutionStatus.reconcile_required
            outcome = DocumentAutomationReconcileResult.document_missing
        elif execution.email_status in {DocumentAutomationEmailStatus.failed, DocumentAutomationEmailStatus.skipped}:
            execution.status = DocumentAutomationExecutionStatus.partially_succeeded
            outcome = DocumentAutomationReconcileResult.email_pending
        elif execution.n8n_status in {DocumentAutomationN8nStatus.failed, DocumentAutomationN8nStatus.skipped}:
            execution.status = DocumentAutomationExecutionStatus.partially_succeeded
            outcome = DocumentAutomationReconcileResult.n8n_pending
        else:
            execution.status = DocumentAutomationExecutionStatus.succeeded
            outcome = DocumentAutomationReconcileResult.in_sync
        self.db.commit()
        self.db.refresh(execution)
        return DocumentAutomationReconcileRead(result=outcome, execution=read_automation_execution(execution))

    def _execute(self, execution: DocumentAutomationExecution, *, actor: User | None) -> DocumentAutomationExecution:
        execution.status = DocumentAutomationExecutionStatus.running
        execution.started_at = datetime.now(UTC)
        execution.error_code = None
        execution.error_message = None
        self.db.commit()
        rule = execution.rule
        try:
            document = self._ensure_document(execution, actor)
            execution.generated_document_id = document.id
            if document.status == AppointmentGeneratedDocumentStatus.failed:
                return self._finish(execution, DocumentAutomationExecutionStatus.failed, "document_automation_generation_failed")
            email_status = self._send_email(rule, execution, document)
            n8n_status = self._emit_n8n(rule, execution, document)
            execution.email_status = email_status
            execution.n8n_status = n8n_status
            if document.status in {AppointmentGeneratedDocumentStatus.partially_generated, AppointmentGeneratedDocumentStatus.reconcile_required}:
                return self._finish(execution, DocumentAutomationExecutionStatus.partially_succeeded, "document_automation_sharing_failed")
            if email_status == DocumentAutomationEmailStatus.failed:
                return self._finish(execution, DocumentAutomationExecutionStatus.partially_succeeded, "document_automation_email_failed")
            if n8n_status == DocumentAutomationN8nStatus.failed:
                return self._finish(execution, DocumentAutomationExecutionStatus.partially_succeeded, "document_automation_n8n_failed")
            if email_status == DocumentAutomationEmailStatus.skipped and rule.email_delivery_enabled:
                return self._finish(execution, DocumentAutomationExecutionStatus.partially_succeeded, "document_automation_sharing_failed")
            return self._finish(execution, DocumentAutomationExecutionStatus.succeeded)
        except IntegrationError as exc:
            return self._finish(execution, DocumentAutomationExecutionStatus.failed, exc.code if exc.code.startswith("document_automation") else "document_automation_generation_failed")
        except Exception:
            return self._finish(execution, DocumentAutomationExecutionStatus.failed, "document_automation_generation_failed")

    def _ensure_document(self, execution: DocumentAutomationExecution, actor: User | None) -> AppointmentGeneratedDocument:
        if execution.generated_document_id:
            document = self.db.get(AppointmentGeneratedDocument, execution.generated_document_id)
            if document and document.status == AppointmentGeneratedDocumentStatus.generated:
                return document
            if document:
                return self.docs_service.retry(execution.appointment_id, document.id)
        rule = execution.rule
        return self.docs_service.generate(
            execution.appointment_id,
            GenerateDocumentRequest(template_id=rule.template_id, sharing_policy=rule.sharing_policy, generation_request_id=f"automation:{execution.idempotency_key}"[:120]),
            actor or self._automation_actor(),
        )

    def _send_email(self, rule: GoogleDocsAutomationRule, execution: DocumentAutomationExecution, document: AppointmentGeneratedDocument) -> DocumentAutomationEmailStatus:
        if not rule.email_delivery_enabled or rule.email_recipient_policy == DocumentAutomationEmailRecipientPolicy.none:
            return DocumentAutomationEmailStatus.not_requested
        if execution.email_status == DocumentAutomationEmailStatus.sent:
            return DocumentAutomationEmailStatus.sent
        recipients = self._email_recipients(rule, execution.appointment, document)
        if not recipients:
            return DocumentAutomationEmailStatus.skipped
        body = (
            "RealMeet genero un documento operativo para una reserva.\n\n"
            f"Documento: {document.document_name}\n"
            f"Reserva: {execution.appointment_id}\n"
            f"Enlace: {read_document(document).document_url or 'Disponible en Google Drive'}\n"
        )
        sent = [self.mailer.send("Documento de RealMeet disponible", email, body) for email in recipients]
        return DocumentAutomationEmailStatus.sent if all(sent) else DocumentAutomationEmailStatus.failed

    def _email_recipients(self, rule: GoogleDocsAutomationRule, appointment: Appointment, document: AppointmentGeneratedDocument) -> list[str]:
        if document.sharing_policy == GoogleDocsSharingPolicy.private or document.sharing_status not in {
            AppointmentGeneratedDocumentSharingStatus.shared,
            AppointmentGeneratedDocumentSharingStatus.partially_shared,
        }:
            return []
        recipients: list[str] = []
        if rule.email_recipient_policy in {DocumentAutomationEmailRecipientPolicy.professional, DocumentAutomationEmailRecipientPolicy.professional_and_client}:
            recipients.append(appointment.professional.user.email)
        if rule.email_recipient_policy in {DocumentAutomationEmailRecipientPolicy.client, DocumentAutomationEmailRecipientPolicy.professional_and_client}:
            if document.sharing_policy == GoogleDocsSharingPolicy.professional_and_client:
                recipients.append(appointment.client.user.email)
        return [item for item in recipients if item and "@" in item]

    def _emit_n8n(self, rule: GoogleDocsAutomationRule, execution: DocumentAutomationExecution, document: AppointmentGeneratedDocument) -> DocumentAutomationN8nStatus:
        if not rule.n8n_event_enabled:
            return DocumentAutomationN8nStatus.not_requested
        if execution.n8n_status == DocumentAutomationN8nStatus.delivered:
            return DocumentAutomationN8nStatus.delivered
        event = DomainEvent.create(
            event_type=WebhookEventType.document_generated,
            entity_type="document",
            entity_id=document.id,
            correlation_id=execution.idempotency_key,
            payload={
                "schema_version": "1.0",
                "event_type": WebhookEventType.document_generated.value,
                "document": {"id": document.id, "document_type": document.template.document_type.value, "status": document.status.value, "document_url": read_document(document).document_url},
                "appointment": {"id": execution.appointment_id},
            },
        )
        deliveries = self.webhook_service.publish(event)
        if not deliveries:
            return DocumentAutomationN8nStatus.skipped
        return DocumentAutomationN8nStatus.delivered if all(item.status == WebhookDeliveryStatus.succeeded for item in deliveries) else DocumentAutomationN8nStatus.failed

    def _finish(self, execution: DocumentAutomationExecution, status: DocumentAutomationExecutionStatus, code: str | None = None) -> DocumentAutomationExecution:
        execution.status = status
        execution.finished_at = datetime.now(UTC)
        execution.error_code = code
        execution.error_message = automation_safe_message(code) if code else None
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def _assert_google_integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration or integration.provider != IntegrationProvider.google_meet:
            raise IntegrationConfigurationError("Google Docs requiere una integracion Google", code="document_automation_rule_invalid")
        return integration

    def _template(self, integration_id: int, template_id: int, *, require_enabled: bool) -> GoogleDocsTemplate:
        self._assert_google_integration(integration_id)
        template = self.db.get(GoogleDocsTemplate, template_id)
        if not template or template.integration_id != integration_id:
            raise IntegrationConfigurationError("Plantilla no encontrada", code="google_docs_template_not_found")
        if require_enabled and not template.enabled:
            raise IntegrationConfigurationError("La plantilla esta deshabilitada", code="document_automation_template_disabled")
        return template

    def _appointment(self, appointment_id: int) -> Appointment:
        appointment = self.db.scalar(
            select(Appointment)
            .options(selectinload(Appointment.professional).selectinload(ProfessionalProfile.user), selectinload(Appointment.client).selectinload(ClientProfile.user))
            .where(Appointment.id == appointment_id)
        )
        if not appointment:
            raise IntegrationConfigurationError("Reserva no encontrada", code="appointment_not_found")
        return appointment

    def _automation_actor(self) -> User:
        actor = self.db.scalar(select(User).where(User.role == UserRole.admin, User.is_active.is_(True)).order_by(User.id.asc()))
        if not actor:
            raise IntegrationProviderExecutionError("No hay administrador activo para automatizacion documental", code="document_automation_rule_invalid")
        return actor
