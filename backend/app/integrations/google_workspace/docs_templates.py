from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db.session import Base
from app.integrations.enums import IntegrationProvider
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationError, IntegrationProviderExecutionError
from app.integrations.google_oauth import GoogleOAuthService
from app.integrations.google_workspace.clients import GoogleDocsClient, GoogleDriveClient
from app.integrations.google_workspace.enums import GoogleWorkspaceServiceKey
from app.integrations.google_workspace.scopes import SERVICE_DEFINITIONS
from app.integrations.google_workspace.service import GoogleWorkspaceService
from app.models.appointment import Appointment
from app.models.integration import GoogleWorkspaceSettings, Integration
from app.models.user import User


GOOGLE_DOC_MIME_TYPE = "application/vnd.google-apps.document"
ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{10,220}$")
PLACEHOLDER_PATTERN = re.compile(r"\{\{[a-zA-Z0-9_]+\}\}")


class GoogleDocsDocumentType(str, enum.Enum):
    appointment_summary = "appointment_summary"
    appointment_confirmation = "appointment_confirmation"
    pre_session_instructions = "pre_session_instructions"
    post_session_instructions = "post_session_instructions"
    administrative_receipt = "administrative_receipt"
    custom_operational = "custom_operational"


class GoogleDocsSharingPolicy(str, enum.Enum):
    private = "private"
    professional_only = "professional_only"
    professional_and_client = "professional_and_client"


class AppointmentGeneratedDocumentStatus(str, enum.Enum):
    pending = "pending"
    generated = "generated"
    partially_generated = "partially_generated"
    failed = "failed"
    reconcile_required = "reconcile_required"


class AppointmentGeneratedDocumentSharingStatus(str, enum.Enum):
    not_requested = "not_requested"
    private = "private"
    shared = "shared"
    partially_shared = "partially_shared"
    failed = "failed"


@dataclass(frozen=True)
class TemplateVariable:
    key: str
    label: str
    description: str
    source: str
    sensitive: bool
    supported_document_types: tuple[GoogleDocsDocumentType, ...]

    @property
    def placeholder(self) -> str:
        return "{{" + self.key + "}}"


ALL_DOCUMENT_TYPES = tuple(GoogleDocsDocumentType)
VARIABLE_REGISTRY: dict[str, TemplateVariable] = {
    "appointment_id": TemplateVariable("appointment_id", "ID reserva", "Identificador de la reserva.", "appointment", False, ALL_DOCUMENT_TYPES),
    "appointment_status": TemplateVariable("appointment_status", "Estado", "Estado actual de la reserva.", "appointment", False, ALL_DOCUMENT_TYPES),
    "appointment_start": TemplateVariable("appointment_start", "Inicio", "Fecha y hora de inicio.", "appointment", False, ALL_DOCUMENT_TYPES),
    "appointment_end": TemplateVariable("appointment_end", "Termino", "Fecha y hora de termino.", "appointment", False, ALL_DOCUMENT_TYPES),
    "appointment_timezone": TemplateVariable("appointment_timezone", "Zona horaria", "Zona horaria operacional.", "system", False, ALL_DOCUMENT_TYPES),
    "professional_name": TemplateVariable("professional_name", "Profesional", "Nombre del profesional.", "professional", False, ALL_DOCUMENT_TYPES),
    "professional_email": TemplateVariable("professional_email", "Email profesional", "Correo del profesional.", "professional", False, ALL_DOCUMENT_TYPES),
    "client_name": TemplateVariable("client_name", "Cliente", "Nombre del cliente.", "client", False, ALL_DOCUMENT_TYPES),
    "client_email": TemplateVariable("client_email", "Email cliente", "Correo del cliente.", "client", False, ALL_DOCUMENT_TYPES),
    "meeting_provider": TemplateVariable("meeting_provider", "Proveedor reunion", "Proveedor de reunion.", "appointment", False, ALL_DOCUMENT_TYPES),
    "meeting_url": TemplateVariable("meeting_url", "URL reunion", "Enlace de reunion si existe.", "appointment", False, ALL_DOCUMENT_TYPES),
    "generated_at": TemplateVariable("generated_at", "Generado", "Fecha de generacion.", "system", False, ALL_DOCUMENT_TYPES),
    "service_name": TemplateVariable("service_name", "Servicio", "Tipo de atencion.", "appointment", False, ALL_DOCUMENT_TYPES),
    "consultation_mode": TemplateVariable("consultation_mode", "Modalidad", "Modalidad de consulta.", "appointment", False, ALL_DOCUMENT_TYPES),
    "cancellation_reason_summary": TemplateVariable("cancellation_reason_summary", "Resumen cancelacion", "Resumen administrativo de cancelacion.", "appointment", False, ALL_DOCUMENT_TYPES),
}
BLOCKED_VARIABLES = {"clinical_notes", "diagnosis", "medical_history", "session_notes", "password", "token"}


class GoogleDocsTemplate(Base):
    __tablename__ = "google_docs_templates"
    __table_args__ = (
        UniqueConstraint("integration_id", "source_document_id", name="uq_google_docs_template_source"),
        Index("ix_google_docs_templates_integration", "integration_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    document_type: Mapped[GoogleDocsDocumentType] = mapped_column(Enum(GoogleDocsDocumentType, name="google_docs_document_type"), nullable=False)
    source_document_id: Mapped[str] = mapped_column(String(220), nullable=False)
    destination_folder_id: Mapped[str | None] = mapped_column(String(220))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_variables: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sharing_policy: Mapped[GoogleDocsSharingPolicy] = mapped_column(Enum(GoogleDocsSharingPolicy, name="google_docs_sharing_policy"), default=GoogleDocsSharingPolicy.private, nullable=False)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_validation_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_validation_error_code: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    integration: Mapped[Integration] = relationship("Integration")


class AppointmentGeneratedDocument(Base):
    __tablename__ = "appointment_generated_documents"
    __table_args__ = (
        UniqueConstraint("appointment_id", "template_id", "generation_request_id", name="uq_appointment_generated_document_request"),
        Index("ix_appointment_generated_documents_appointment", "appointment_id"),
        Index("ix_appointment_generated_documents_template", "template_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[int] = mapped_column(ForeignKey("google_docs_templates.id", ondelete="CASCADE"), nullable=False)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider, name="integration_provider"), nullable=False)
    external_document_id: Mapped[str | None] = mapped_column(String(220))
    external_file_id: Mapped[str | None] = mapped_column(String(220))
    document_name: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[AppointmentGeneratedDocumentStatus] = mapped_column(Enum(AppointmentGeneratedDocumentStatus, name="appointment_generated_document_status"), default=AppointmentGeneratedDocumentStatus.pending, nullable=False)
    sharing_status: Mapped[AppointmentGeneratedDocumentSharingStatus] = mapped_column(Enum(AppointmentGeneratedDocumentSharingStatus, name="appointment_generated_document_sharing_status"), default=AppointmentGeneratedDocumentSharingStatus.not_requested, nullable=False)
    sharing_policy: Mapped[GoogleDocsSharingPolicy] = mapped_column(Enum(GoogleDocsSharingPolicy, name="google_docs_sharing_policy"), default=GoogleDocsSharingPolicy.private, nullable=False)
    generation_request_id: Mapped[str] = mapped_column(String(180), nullable=False)
    generated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(120))
    last_error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    appointment: Mapped[Appointment] = relationship("Appointment")
    template: Mapped[GoogleDocsTemplate] = relationship("GoogleDocsTemplate")


class GoogleDocsTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    document_type: GoogleDocsDocumentType
    source_document_id: str = Field(min_length=10, max_length=220)
    destination_folder_id: str | None = Field(default=None, max_length=220)
    enabled: bool = True
    allowed_variables: list[str] = Field(default_factory=list)
    sharing_policy: GoogleDocsSharingPolicy = GoogleDocsSharingPolicy.private

    @field_validator("source_document_id", "destination_folder_id")
    @classmethod
    def validate_id(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        extracted = extract_google_id(value.strip())
        if not extracted:
            raise ValueError("ID Google invalido")
        return extracted

    @field_validator("allowed_variables")
    @classmethod
    def validate_variables(cls, value: list[str]) -> list[str]:
        return validate_allowed_variables(value)


class GoogleDocsTemplateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    destination_folder_id: str | None = Field(default=None, max_length=220)
    allowed_variables: list[str] | None = None
    sharing_policy: GoogleDocsSharingPolicy | None = None

    @field_validator("destination_folder_id")
    @classmethod
    def validate_id(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        extracted = extract_google_id(value.strip())
        if not extracted:
            raise ValueError("ID Google invalido")
        return extracted

    @field_validator("allowed_variables")
    @classmethod
    def validate_variables(cls, value: list[str] | None) -> list[str] | None:
        return validate_allowed_variables(value) if value is not None else None


class GoogleDocsTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: int
    name: str
    description: str | None
    document_type: GoogleDocsDocumentType
    source_document_id: str
    destination_folder_id: str | None
    enabled: bool
    allowed_variables: list[str]
    sharing_policy: GoogleDocsSharingPolicy
    last_validated_at: datetime | None
    last_validation_error_at: datetime | None
    last_validation_error_code: str | None
    created_at: datetime
    updated_at: datetime


class GoogleDocsTemplateValidationRead(BaseModel):
    valid: bool
    document: dict[str, str | None]
    folder: dict[str, str | None] | None
    placeholders: list[str]
    unknown_variables: list[str]


class TemplateVariableRead(BaseModel):
    key: str
    placeholder: str
    label: str
    description: str
    source: str
    sensitive: bool
    supported_document_types: list[GoogleDocsDocumentType]


class GenerateDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: int
    sharing_policy: GoogleDocsSharingPolicy | None = None
    generation_request_id: str = Field(min_length=6, max_length=120)


class AppointmentGeneratedDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    template_id: int
    integration_id: int
    provider: IntegrationProvider
    external_document_id: str | None
    external_file_id: str | None
    document_name: str
    status: AppointmentGeneratedDocumentStatus
    sharing_status: AppointmentGeneratedDocumentSharingStatus
    sharing_policy: GoogleDocsSharingPolicy
    generation_request_id: str
    generated_by_user_id: int | None
    generated_at: datetime | None
    last_error_at: datetime | None
    last_error_code: str | None
    last_error_message: str | None
    created_at: datetime
    updated_at: datetime
    document_url: str | None = None


class ReconcileDocumentRead(BaseModel):
    result: str
    document: AppointmentGeneratedDocumentRead


def extract_google_id(value: str) -> str | None:
    if "/document/d/" in value:
        match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", value)
        return match.group(1) if match and ID_PATTERN.match(match.group(1)) else None
    if "/folders/" in value:
        match = re.search(r"/folders/([a-zA-Z0-9_-]+)", value)
        return match.group(1) if match and ID_PATTERN.match(match.group(1)) else None
    return value if ID_PATTERN.match(value) else None


def validate_allowed_variables(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in values:
        key = item.strip().removeprefix("{{").removesuffix("}}")
        if key in BLOCKED_VARIABLES or key not in VARIABLE_REGISTRY:
            raise ValueError("Variable no permitida")
        if key not in normalized:
            normalized.append(key)
    return normalized


def variable_catalog() -> list[TemplateVariableRead]:
    return [
        TemplateVariableRead(
            key=item.key,
            placeholder=item.placeholder,
            label=item.label,
            description=item.description,
            source=item.source,
            sensitive=item.sensitive,
            supported_document_types=list(item.supported_document_types),
        )
        for item in VARIABLE_REGISTRY.values()
    ]


def safe_message(code: str) -> str:
    messages = {
        "google_docs_disabled": "Google Docs esta deshabilitado.",
        "google_docs_not_authorized": "Google Docs requiere autorizacion.",
        "google_drive_disabled": "Google Drive esta deshabilitado.",
        "google_drive_not_authorized": "Google Drive requiere autorizacion.",
        "google_docs_template_not_found": "No encontramos la plantilla Google Docs.",
        "google_drive_folder_not_found": "No encontramos la carpeta destino.",
        "google_docs_unknown_variable": "La plantilla contiene variables no permitidas.",
        "google_docs_copy_failed": "No pudimos copiar la plantilla.",
        "google_docs_replace_failed": "No pudimos reemplazar variables.",
        "google_drive_share_failed": "No pudimos compartir el documento.",
        "google_generated_document_not_found": "No encontramos el documento generado.",
        "google_docs_generation_failed": "No pudimos generar el documento.",
    }
    return messages.get(code, "No pudimos completar la operacion Google Docs.")


class GoogleDocsTemplateService:
    def __init__(self, db: Session, *, oauth_service: GoogleOAuthService | None = None, drive_client: GoogleDriveClient | None = None, docs_client: GoogleDocsClient | None = None) -> None:
        self.db = db
        self.oauth_service = oauth_service or GoogleOAuthService(db)
        self.drive_client = drive_client or GoogleDriveClient()
        self.docs_client = docs_client or GoogleDocsClient()

    def list_templates(self, integration_id: int) -> list[GoogleDocsTemplate]:
        self._assert_integration(integration_id)
        return list(self.db.scalars(select(GoogleDocsTemplate).where(GoogleDocsTemplate.integration_id == integration_id).order_by(GoogleDocsTemplate.created_at.desc())))

    def create_template(self, integration_id: int, payload: GoogleDocsTemplateCreate) -> GoogleDocsTemplate:
        self._assert_ready(integration_id)
        if self.db.scalar(select(GoogleDocsTemplate).where(GoogleDocsTemplate.integration_id == integration_id, GoogleDocsTemplate.source_document_id == payload.source_document_id)):
            raise IntegrationConfigurationError("Ya existe una plantilla para ese documento origen", code="google_docs_template_duplicate")
        item = GoogleDocsTemplate(integration_id=integration_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_template(self, integration_id: int, template_id: int) -> GoogleDocsTemplate:
        self._assert_integration(integration_id)
        item = self.db.get(GoogleDocsTemplate, template_id)
        if not item or item.integration_id != integration_id:
            raise IntegrationConfigurationError("Plantilla no encontrada", code="google_docs_template_not_found")
        return item

    def update_template(self, integration_id: int, template_id: int, payload: GoogleDocsTemplateUpdate) -> GoogleDocsTemplate:
        item = self.get_template(integration_id, template_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        return item

    def set_enabled(self, integration_id: int, template_id: int, enabled: bool) -> GoogleDocsTemplate:
        item = self.get_template(integration_id, template_id)
        item.enabled = enabled
        self.db.commit()
        self.db.refresh(item)
        return item

    def validate_template(self, integration_id: int, template_id: int) -> GoogleDocsTemplateValidationRead:
        item = self.get_template(integration_id, template_id)
        try:
            token = self._access_token_ready(integration_id)
            metadata = self._source_doc_metadata(token, item.source_document_id)
            folder = self.drive_client.get_folder_metadata(access_token=token, folder_id=item.destination_folder_id) if item.destination_folder_id else None
            doc = self.docs_client.get_document(access_token=token, document_id=item.source_document_id)
            placeholders = sorted(set(PLACEHOLDER_PATTERN.findall(doc.get("text") or "")))
            unknown = [placeholder for placeholder in placeholders if placeholder.removeprefix("{{").removesuffix("}}") not in item.allowed_variables]
            if unknown:
                raise IntegrationConfigurationError("La plantilla contiene variables no permitidas", code="google_docs_unknown_variable")
            item.last_validated_at = datetime.now(UTC)
            item.last_validation_error_at = None
            item.last_validation_error_code = None
            self.db.commit()
            return GoogleDocsTemplateValidationRead(valid=True, document={"id": metadata["id"], "name": metadata["name"]}, folder=folder, placeholders=placeholders, unknown_variables=[])
        except IntegrationError as exc:
            item.last_validation_error_at = datetime.now(UTC)
            item.last_validation_error_code = exc.code
            self.db.commit()
            raise

    def list_documents(self, appointment_id: int) -> list[AppointmentGeneratedDocument]:
        return list(self.db.scalars(select(AppointmentGeneratedDocument).where(AppointmentGeneratedDocument.appointment_id == appointment_id).order_by(AppointmentGeneratedDocument.created_at.desc())))

    def get_document(self, appointment_id: int, document_id: int) -> AppointmentGeneratedDocument:
        doc = self.db.get(AppointmentGeneratedDocument, document_id)
        if not doc or doc.appointment_id != appointment_id:
            raise IntegrationConfigurationError("Documento generado no encontrado", code="google_generated_document_not_found")
        return doc

    def generate(self, appointment_id: int, payload: GenerateDocumentRequest, admin_user: User) -> AppointmentGeneratedDocument:
        template = self.db.get(GoogleDocsTemplate, payload.template_id)
        if not template or not template.enabled:
            raise IntegrationConfigurationError("Plantilla no encontrada o deshabilitada", code="google_docs_template_not_found")
        appointment = self._appointment(appointment_id)
        existing = self.db.scalar(select(AppointmentGeneratedDocument).where(AppointmentGeneratedDocument.appointment_id == appointment_id, AppointmentGeneratedDocument.template_id == template.id, AppointmentGeneratedDocument.generation_request_id == payload.generation_request_id))
        if existing:
            return existing
        policy = payload.sharing_policy or template.sharing_policy
        name = f"RealMeet - {template.document_type.value} - Reserva {appointment.id}"
        doc = AppointmentGeneratedDocument(
            appointment_id=appointment.id,
            template_id=template.id,
            integration_id=template.integration_id,
            provider=IntegrationProvider.google_meet,
            document_name=name,
            status=AppointmentGeneratedDocumentStatus.pending,
            sharing_status=AppointmentGeneratedDocumentSharingStatus.not_requested,
            sharing_policy=policy,
            generation_request_id=payload.generation_request_id,
            generated_by_user_id=admin_user.id,
        )
        self.db.add(doc)
        self.db.commit()
        return self._generate_existing(doc)

    def retry(self, appointment_id: int, document_id: int) -> AppointmentGeneratedDocument:
        doc = self.get_document(appointment_id, document_id)
        if doc.status not in {AppointmentGeneratedDocumentStatus.failed, AppointmentGeneratedDocumentStatus.partially_generated, AppointmentGeneratedDocumentStatus.reconcile_required}:
            raise IntegrationConfigurationError("Solo se pueden reintentar documentos fallidos o parciales", code="google_docs_retry_not_allowed")
        return self._generate_existing(doc)

    def reconcile(self, appointment_id: int, document_id: int) -> ReconcileDocumentRead:
        doc = self.get_document(appointment_id, document_id)
        if not doc.external_file_id:
            doc.status = AppointmentGeneratedDocumentStatus.failed
            doc.last_error_code = "google_generated_document_not_found"
            doc.last_error_message = safe_message(doc.last_error_code)
            self.db.commit()
            return ReconcileDocumentRead(result="external_document_missing", document=read_document(doc))
        try:
            token = self._access_token_ready(doc.integration_id)
            metadata = self.drive_client.get_file_metadata(access_token=token, file_id=doc.external_file_id)
            if metadata.get("mime_type") != GOOGLE_DOC_MIME_TYPE or metadata.get("trashed"):
                doc.status = AppointmentGeneratedDocumentStatus.reconcile_required
                result = "external_document_missing"
            else:
                doc.status = AppointmentGeneratedDocumentStatus.generated if doc.sharing_status != AppointmentGeneratedDocumentSharingStatus.failed else AppointmentGeneratedDocumentStatus.partially_generated
                result = "external_document_found"
            self.db.commit()
            return ReconcileDocumentRead(result=result, document=read_document(doc))
        except IntegrationError:
            doc.status = AppointmentGeneratedDocumentStatus.reconcile_required
            doc.last_error_code = "google_generated_document_not_found"
            doc.last_error_message = safe_message(doc.last_error_code)
            self.db.commit()
            return ReconcileDocumentRead(result="external_document_missing", document=read_document(doc))

    def _generate_existing(self, doc: AppointmentGeneratedDocument) -> AppointmentGeneratedDocument:
        template = doc.template
        appointment = doc.appointment
        try:
            token = self._access_token_ready(template.integration_id)
            if not doc.external_file_id:
                self._source_doc_metadata(token, template.source_document_id)
                copied = self.drive_client.copy_file(
                    access_token=token,
                    file_id=template.source_document_id,
                    name=doc.document_name,
                    app_properties={"realmeet_appointment_id": str(appointment.id), "realmeet_template_id": str(template.id), "realmeet_generated_document_id": str(doc.id)},
                )
                doc.external_file_id = copied["id"]
                doc.external_document_id = copied["id"]
                if template.destination_folder_id:
                    self.drive_client.move_file(access_token=token, file_id=doc.external_file_id, folder_id=template.destination_folder_id)
            replacements = self._replacements(appointment, template.allowed_variables)
            self.docs_client.replace_all_text(access_token=token, document_id=doc.external_document_id or doc.external_file_id, replacements=replacements)
            sharing_status = self._share(token, doc, appointment)
            doc.sharing_status = sharing_status
            doc.status = AppointmentGeneratedDocumentStatus.generated if sharing_status != AppointmentGeneratedDocumentSharingStatus.failed else AppointmentGeneratedDocumentStatus.partially_generated
            doc.generated_at = datetime.now(UTC)
            doc.last_error_at = None
            doc.last_error_code = None
            doc.last_error_message = None
        except IntegrationError as exc:
            doc.status = AppointmentGeneratedDocumentStatus.partially_generated if doc.external_file_id else AppointmentGeneratedDocumentStatus.failed
            doc.sharing_status = AppointmentGeneratedDocumentSharingStatus.failed if exc.code == "google_drive_share_failed" else doc.sharing_status
            doc.last_error_at = datetime.now(UTC)
            doc.last_error_code = exc.code
            doc.last_error_message = safe_message(exc.code)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def _share(self, token: str, doc: AppointmentGeneratedDocument, appointment: Appointment) -> AppointmentGeneratedDocumentSharingStatus:
        if doc.sharing_policy == GoogleDocsSharingPolicy.private:
            return AppointmentGeneratedDocumentSharingStatus.private
        emails = [appointment.professional.user.email]
        if doc.sharing_policy == GoogleDocsSharingPolicy.professional_and_client:
            emails.append(appointment.client.user.email)
        shared = 0
        for email in emails:
            if not email or "@" not in email:
                continue
            self.drive_client.create_permission(access_token=token, file_id=doc.external_file_id, email=email, role="reader")
            shared += 1
        if shared == len(emails):
            return AppointmentGeneratedDocumentSharingStatus.shared
        if shared:
            return AppointmentGeneratedDocumentSharingStatus.partially_shared
        raise IntegrationProviderExecutionError("No pudimos compartir el documento", code="google_drive_share_failed")

    def _source_doc_metadata(self, token: str, document_id: str) -> dict:
        metadata = self.drive_client.get_file_metadata(access_token=token, file_id=document_id)
        if metadata.get("mime_type") != GOOGLE_DOC_MIME_TYPE or metadata.get("trashed"):
            raise IntegrationConfigurationError("La plantilla no es un Google Doc valido", code="google_docs_invalid_template")
        return metadata

    def _assert_integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration or integration.provider != IntegrationProvider.google_meet:
            raise IntegrationConfigurationError("Google Docs requiere una integracion Google", code="google_docs_google_integration_required")
        return integration

    def _access_token_ready(self, integration_id: int) -> str:
        self._assert_ready(integration_id)
        return self.oauth_service.access_token(integration_id)

    def _assert_ready(self, integration_id: int) -> tuple[Integration, GoogleWorkspaceSettings]:
        integration = self._assert_integration(integration_id)
        settings = GoogleWorkspaceService(self.db, oauth_service=self.oauth_service).settings(integration_id)
        if not settings.docs_enabled:
            raise IntegrationConfigurationError("Google Docs esta deshabilitado", code="google_docs_disabled")
        if not settings.drive_enabled:
            raise IntegrationConfigurationError("Google Drive esta deshabilitado", code="google_drive_disabled")
        credential = self.oauth_service._active_credential(integration_id)
        scopes = set(credential.scopes if credential else [])
        if not set(SERVICE_DEFINITIONS[GoogleWorkspaceServiceKey.docs].required_scopes).issubset(scopes):
            raise IntegrationConfigurationError("Google Docs requiere autorizacion", code="google_docs_not_authorized")
        if not set(SERVICE_DEFINITIONS[GoogleWorkspaceServiceKey.drive].required_scopes).issubset(scopes):
            raise IntegrationConfigurationError("Google Drive requiere autorizacion", code="google_drive_not_authorized")
        return integration, settings

    def _appointment(self, appointment_id: int) -> Appointment:
        appointment = self.db.get(Appointment, appointment_id)
        if not appointment:
            raise IntegrationConfigurationError("Reserva no encontrada", code="appointment_not_found")
        return appointment

    def _replacements(self, appointment: Appointment, allowed_variables: list[str]) -> dict[str, str]:
        professional = appointment.professional.user
        client = appointment.client.user
        meeting_url = appointment.meeting_link.meeting_url if appointment.meeting_link and appointment.meeting_link.meeting_url else appointment.meeting_url
        values = {
            "appointment_id": str(appointment.id),
            "appointment_status": appointment.status.value,
            "appointment_start": _iso(appointment.start_datetime),
            "appointment_end": _iso(appointment.end_datetime),
            "appointment_timezone": "America/Santiago",
            "professional_name": _full_name(professional),
            "professional_email": professional.email,
            "client_name": _full_name(client),
            "client_email": client.email,
            "meeting_provider": appointment.meeting_provider.value if appointment.meeting_provider else "",
            "meeting_url": meeting_url or "",
            "generated_at": _iso(datetime.now(UTC)),
            "service_name": "",
            "consultation_mode": appointment.consultation_mode.value if appointment.consultation_mode else "",
            "cancellation_reason_summary": "Cancelada" if appointment.cancellation_reason else "",
        }
        return {VARIABLE_REGISTRY[key].placeholder: values.get(key, "") for key in allowed_variables if key in VARIABLE_REGISTRY}


def read_document(doc: AppointmentGeneratedDocument) -> AppointmentGeneratedDocumentRead:
    data = AppointmentGeneratedDocumentRead.model_validate(doc)
    data.document_url = f"https://docs.google.com/document/d/{doc.external_document_id}/edit" if doc.external_document_id else None
    return data


def _full_name(user: User) -> str:
    return f"{user.first_name} {user.last_name}".strip()


def _iso(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()
