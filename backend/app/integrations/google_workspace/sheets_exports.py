from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db.session import Base
from app.integrations.enums import IntegrationProvider
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationError, IntegrationProviderExecutionError
from app.integrations.google_oauth import GoogleOAuthService
from app.integrations.google_workspace.clients import GoogleSheetsClient
from app.integrations.google_workspace.enums import GoogleWorkspaceServiceKey
from app.integrations.google_workspace.scopes import SERVICE_DEFINITIONS
from app.integrations.google_workspace.service import GoogleWorkspaceService
from app.models.appointment import Appointment, AppointmentStatus
from app.models.client_profile import ClientProfile
from app.models.integration import GoogleWorkspaceSettings, Integration
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User


SHEETS_EXPORT_COLUMNS = [
    "realmeet_appointment_id",
    "status",
    "starts_at",
    "ends_at",
    "timezone",
    "professional_name",
    "professional_email",
    "client_name",
    "client_email",
    "meeting_provider",
    "meeting_url",
    "created_at",
    "updated_at",
    "cancelled_at",
]
SPREADSHEET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{10,200}$")
MAX_EXPORT_DAYS = 366
MAX_EXPORT_RECORDS = 1000


class GoogleSheetsExportMode(str, enum.Enum):
    upsert = "upsert"
    append_only = "append_only"


class GoogleSheetsExportExecutionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    partially_succeeded = "partially_succeeded"
    failed = "failed"


class GoogleSheetsExportConfig(Base):
    __tablename__ = "google_sheets_export_configs"
    __table_args__ = (
        UniqueConstraint("integration_id", "spreadsheet_id", "sheet_name", name="uq_google_sheets_export_destination"),
        Index("ix_google_sheets_export_configs_integration", "integration_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    spreadsheet_id: Mapped[str] = mapped_column(String(220), nullable=False)
    sheet_name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    export_mode: Mapped[GoogleSheetsExportMode] = mapped_column(Enum(GoogleSheetsExportMode, name="google_sheets_export_mode"), default=GoogleSheetsExportMode.upsert, nullable=False)
    date_range_mode: Mapped[str] = mapped_column(String(40), default="custom", nullable=False)
    include_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    integration: Mapped[Integration] = relationship("Integration")
    executions: Mapped[list["GoogleSheetsExportExecution"]] = relationship("GoogleSheetsExportExecution", back_populates="config", cascade="all, delete-orphan")


class GoogleSheetsExportExecution(Base):
    __tablename__ = "google_sheets_export_executions"
    __table_args__ = (
        Index("ix_google_sheets_export_executions_config", "config_id"),
        Index("ix_google_sheets_export_executions_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    config_id: Mapped[int] = mapped_column(ForeignKey("google_sheets_export_configs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[GoogleSheetsExportExecutionStatus] = mapped_column(Enum(GoogleSheetsExportExecutionStatus, name="google_sheets_export_execution_status"), default=GoogleSheetsExportExecutionStatus.pending, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    include_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inserted_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(120))
    error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    config: Mapped[GoogleSheetsExportConfig] = relationship("GoogleSheetsExportConfig", back_populates="executions")


class GoogleSheetsExportConfigCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    spreadsheet_id: str = Field(min_length=10, max_length=220)
    sheet_name: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    export_mode: GoogleSheetsExportMode = GoogleSheetsExportMode.upsert
    date_range_mode: str = "custom"
    include_cancelled: bool = False

    @field_validator("spreadsheet_id")
    @classmethod
    def validate_spreadsheet_id(cls, value: str) -> str:
        normalized = extract_spreadsheet_id(value.strip())
        if not normalized:
            raise ValueError("spreadsheet_id debe ser un identificador valido")
        return normalized

    @field_validator("sheet_name", "name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("El campo no puede estar vacio")
        return stripped


class GoogleSheetsExportConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    spreadsheet_id: str | None = Field(default=None, min_length=10, max_length=220)
    sheet_name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None
    export_mode: GoogleSheetsExportMode | None = None
    include_cancelled: bool | None = None

    @field_validator("spreadsheet_id")
    @classmethod
    def validate_spreadsheet_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = extract_spreadsheet_id(value.strip())
        if not normalized:
            raise ValueError("spreadsheet_id debe ser un identificador valido")
        return normalized

    @field_validator("sheet_name", "name")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("El campo no puede estar vacio")
        return stripped


class GoogleSheetsExportRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_from: datetime
    starts_to: datetime
    include_cancelled: bool | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "GoogleSheetsExportRunRequest":
        if self.starts_from.tzinfo is None or self.starts_to.tzinfo is None:
            raise ValueError("El rango debe incluir timezone")
        if self.starts_from >= self.starts_to:
            raise ValueError("starts_from debe ser menor que starts_to")
        if self.starts_to - self.starts_from > timedelta(days=MAX_EXPORT_DAYS):
            raise ValueError("El rango no puede superar 366 dias")
        return self


class GoogleSheetsExportConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: int
    name: str
    spreadsheet_id: str
    sheet_name: str
    enabled: bool
    export_mode: GoogleSheetsExportMode
    date_range_mode: str
    include_cancelled: bool
    last_exported_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_code: str | None
    created_at: datetime
    updated_at: datetime


class GoogleSheetsExportExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    config_id: int
    status: GoogleSheetsExportExecutionStatus
    started_at: datetime | None
    finished_at: datetime | None
    requested_by_user_id: int | None
    range_start: datetime
    range_end: datetime
    include_cancelled: bool
    total_records: int
    inserted_records: int
    updated_records: int
    skipped_records: int
    failed_records: int
    error_code: str | None
    error_message: str | None
    created_at: datetime


class GoogleSheetsExportValidationRead(BaseModel):
    valid: bool
    spreadsheet: dict[str, str | None]
    sheet: dict[str, str | None]
    headers: dict[str, str]


@dataclass
class HeaderState:
    status: str
    existing_headers: list[str]


def extract_spreadsheet_id(value: str) -> str | None:
    if "/spreadsheets/d/" in value:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", value)
        return match.group(1) if match and SPREADSHEET_ID_PATTERN.match(match.group(1)) else None
    return value if SPREADSHEET_ID_PATTERN.match(value) else None


def sheet_range(sheet_name: str, range_ref: str) -> str:
    escaped = sheet_name.replace("'", "''")
    return f"'{escaped}'!{range_ref}"


def safe_error_message(code: str) -> str:
    messages = {
        "google_sheets_not_authorized": "Google Sheets requiere autorizacion.",
        "google_sheets_disabled": "Google Sheets esta deshabilitado para esta integracion.",
        "google_spreadsheet_not_found": "No pudimos acceder al spreadsheet indicado.",
        "google_sheet_not_found": "No encontramos la pestana configurada.",
        "google_sheets_incompatible_headers": "La hoja tiene encabezados incompatibles.",
        "google_sheets_rate_limited": "Google Sheets limito temporalmente la operacion.",
        "google_sheets_unavailable": "Google Sheets no esta disponible.",
        "google_sheets_export_failed": "No pudimos completar la exportacion.",
    }
    return messages.get(code, "No pudimos completar la operacion con Google Sheets.")


class GoogleSheetsAppointmentExportService:
    def __init__(
        self,
        db: Session,
        *,
        oauth_service: GoogleOAuthService | None = None,
        sheets_client: GoogleSheetsClient | None = None,
    ) -> None:
        self.db = db
        self.oauth_service = oauth_service or GoogleOAuthService(db)
        self.sheets_client = sheets_client or GoogleSheetsClient()

    def list_configs(self, integration_id: int) -> list[GoogleSheetsExportConfig]:
        self._assert_integration(integration_id)
        return list(self.db.scalars(select(GoogleSheetsExportConfig).where(GoogleSheetsExportConfig.integration_id == integration_id).order_by(GoogleSheetsExportConfig.created_at.desc())))

    def create_config(self, integration_id: int, payload: GoogleSheetsExportConfigCreate) -> GoogleSheetsExportConfig:
        self._assert_ready(integration_id)
        self._assert_unique(integration_id, payload.spreadsheet_id, payload.sheet_name)
        item = GoogleSheetsExportConfig(integration_id=integration_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_config(self, integration_id: int, config_id: int) -> GoogleSheetsExportConfig:
        self._assert_integration(integration_id)
        item = self.db.get(GoogleSheetsExportConfig, config_id)
        if not item or item.integration_id != integration_id:
            raise IntegrationConfigurationError("Configuracion de exportacion no encontrada", code="google_sheets_export_config_not_found")
        return item

    def update_config(self, integration_id: int, config_id: int, payload: GoogleSheetsExportConfigUpdate) -> GoogleSheetsExportConfig:
        item = self.get_config(integration_id, config_id)
        data = payload.model_dump(exclude_unset=True)
        spreadsheet_id = data.get("spreadsheet_id", item.spreadsheet_id)
        sheet_name = data.get("sheet_name", item.sheet_name)
        if spreadsheet_id != item.spreadsheet_id or sheet_name != item.sheet_name:
            self._assert_unique(integration_id, spreadsheet_id, sheet_name, exclude_id=item.id)
        for field, value in data.items():
            setattr(item, field, value)
        item.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        return item

    def validate_config(self, integration_id: int, config_id: int) -> GoogleSheetsExportValidationRead:
        config = self.get_config(integration_id, config_id)
        self._assert_ready(integration_id)
        token = self.oauth_service.access_token(integration_id)
        metadata = self._metadata(token, config.spreadsheet_id)
        sheet = self._find_sheet(metadata, config.sheet_name)
        headers = self._ensure_headers(token, config)
        return GoogleSheetsExportValidationRead(
            valid=True,
            spreadsheet={"title": str(metadata.get("title") or "")},
            sheet={"name": sheet},
            headers={"status": headers.status},
        )

    def list_executions(self, integration_id: int, config_id: int) -> list[GoogleSheetsExportExecution]:
        config = self.get_config(integration_id, config_id)
        return list(self.db.scalars(select(GoogleSheetsExportExecution).where(GoogleSheetsExportExecution.config_id == config.id).order_by(GoogleSheetsExportExecution.created_at.desc()).limit(50)))

    def get_execution(self, integration_id: int, config_id: int, execution_id: int) -> GoogleSheetsExportExecution:
        config = self.get_config(integration_id, config_id)
        execution = self.db.get(GoogleSheetsExportExecution, execution_id)
        if not execution or execution.config_id != config.id:
            raise IntegrationConfigurationError("Ejecucion de exportacion no encontrada", code="google_sheets_export_execution_not_found")
        return execution

    def run_export(self, integration_id: int, config_id: int, payload: GoogleSheetsExportRunRequest, admin_user: User) -> GoogleSheetsExportExecution:
        config = self.get_config(integration_id, config_id)
        include_cancelled = config.include_cancelled if payload.include_cancelled is None else payload.include_cancelled
        execution = self._create_execution(config, payload.starts_from, payload.starts_to, include_cancelled, admin_user)
        self.db.commit()
        try:
            return self._execute(config, execution)
        except IntegrationError as exc:
            return self._fail_execution(config, execution, exc.code, safe_error_message(exc.code))

    def retry_execution(self, integration_id: int, config_id: int, execution_id: int, admin_user: User) -> GoogleSheetsExportExecution:
        previous = self.get_execution(integration_id, config_id, execution_id)
        if previous.status not in {GoogleSheetsExportExecutionStatus.failed, GoogleSheetsExportExecutionStatus.partially_succeeded}:
            raise IntegrationConfigurationError("Solo se pueden reintentar ejecuciones fallidas o parciales", code="google_sheets_retry_not_allowed")
        payload = GoogleSheetsExportRunRequest(starts_from=previous.range_start, starts_to=previous.range_end, include_cancelled=previous.include_cancelled)
        return self.run_export(integration_id, config_id, payload, admin_user)

    def _execute(self, config: GoogleSheetsExportConfig, execution: GoogleSheetsExportExecution) -> GoogleSheetsExportExecution:
        self._assert_ready(config.integration_id)
        token = self.oauth_service.access_token(config.integration_id)
        self._metadata(token, config.spreadsheet_id)
        self._ensure_headers(token, config)
        existing_rows = self.sheets_client.get_sheet_values(access_token=token, spreadsheet_id=config.spreadsheet_id, range_name=sheet_range(config.sheet_name, "A:N"))
        existing_by_id = self._existing_row_index(existing_rows)
        appointments = self._appointments(execution.range_start, execution.range_end, execution.include_cancelled)
        execution.total_records = len(appointments)
        if len(appointments) > MAX_EXPORT_RECORDS:
            raise IntegrationConfigurationError("La exportacion supera el maximo sincronico de 1000 reservas", code="google_sheets_export_too_large")
        rows_to_append: list[list[str]] = []
        updates: list[dict[str, object]] = []
        for appointment in appointments:
            row = self._appointment_row(appointment)
            key = row[0]
            if key in existing_by_id:
                if config.export_mode == GoogleSheetsExportMode.upsert:
                    row_number = existing_by_id[key]
                    updates.append({"range": sheet_range(config.sheet_name, f"A{row_number}:N{row_number}"), "values": [row]})
                    execution.updated_records += 1
                else:
                    execution.skipped_records += 1
            else:
                rows_to_append.append(row)
                execution.inserted_records += 1
        if updates:
            self.sheets_client.batch_update_values(access_token=token, spreadsheet_id=config.spreadsheet_id, data=updates)
        if rows_to_append:
            self.sheets_client.append_sheet_values(access_token=token, spreadsheet_id=config.spreadsheet_id, range_name=sheet_range(config.sheet_name, "A:N"), values=rows_to_append)
        now = datetime.now(UTC)
        execution.status = GoogleSheetsExportExecutionStatus.succeeded
        execution.finished_at = now
        config.last_exported_at = now
        config.last_success_at = now
        config.last_error_at = None
        config.last_error_code = None
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def _create_execution(self, config: GoogleSheetsExportConfig, starts_from: datetime, starts_to: datetime, include_cancelled: bool, admin_user: User) -> GoogleSheetsExportExecution:
        now = datetime.now(UTC)
        execution = GoogleSheetsExportExecution(
            config_id=config.id,
            status=GoogleSheetsExportExecutionStatus.running,
            started_at=now,
            requested_by_user_id=admin_user.id,
            range_start=starts_from,
            range_end=starts_to,
            include_cancelled=include_cancelled,
        )
        self.db.add(execution)
        return execution

    def _fail_execution(self, config: GoogleSheetsExportConfig, execution: GoogleSheetsExportExecution, code: str, message: str) -> GoogleSheetsExportExecution:
        now = datetime.now(UTC)
        execution.status = GoogleSheetsExportExecutionStatus.failed
        execution.finished_at = now
        execution.failed_records = execution.total_records
        execution.error_code = code
        execution.error_message = message
        config.last_error_at = now
        config.last_error_code = code
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def _assert_integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration or integration.provider != IntegrationProvider.google_meet:
            raise IntegrationConfigurationError("Google Sheets requiere una integracion Google", code="google_sheets_google_integration_required")
        return integration

    def _assert_ready(self, integration_id: int) -> tuple[Integration, GoogleWorkspaceSettings]:
        integration = self._assert_integration(integration_id)
        settings = GoogleWorkspaceService(self.db, oauth_service=self.oauth_service).settings(integration_id)
        if not settings.sheets_enabled:
            raise IntegrationConfigurationError("Google Sheets esta deshabilitado para esta integracion", code="google_sheets_disabled")
        credential = self.oauth_service._active_credential(integration_id)
        scopes = credential.scopes if credential else []
        required = set(SERVICE_DEFINITIONS[GoogleWorkspaceServiceKey.sheets].required_scopes)
        if not required.issubset(set(scopes)):
            raise IntegrationConfigurationError("Google Sheets requiere autorizacion", code="google_sheets_not_authorized")
        return integration, settings

    def _assert_unique(self, integration_id: int, spreadsheet_id: str, sheet_name: str, exclude_id: int | None = None) -> None:
        query = select(GoogleSheetsExportConfig).where(
            GoogleSheetsExportConfig.integration_id == integration_id,
            GoogleSheetsExportConfig.spreadsheet_id == spreadsheet_id,
            GoogleSheetsExportConfig.sheet_name == sheet_name,
        )
        existing = self.db.scalar(query)
        if existing and existing.id != exclude_id:
            raise IntegrationConfigurationError("Ya existe una configuracion para ese spreadsheet y pestana", code="google_sheets_export_duplicate")

    def _metadata(self, access_token: str, spreadsheet_id: str) -> dict:
        try:
            metadata = self.sheets_client.get_spreadsheet_metadata(access_token=access_token, spreadsheet_id=spreadsheet_id)
        except IntegrationError:
            raise
        except Exception as exc:
            raise IntegrationProviderExecutionError("Google Sheets no esta disponible", code="google_sheets_unavailable") from exc
        if not metadata:
            raise IntegrationConfigurationError("No pudimos acceder al spreadsheet indicado", code="google_spreadsheet_not_found")
        return metadata

    def _find_sheet(self, metadata: dict, sheet_name: str) -> str:
        sheets = metadata.get("sheets") or []
        names = [str(item.get("title")) for item in sheets if isinstance(item, dict)]
        if sheet_name not in names:
            raise IntegrationConfigurationError("No encontramos la pestana configurada", code="google_sheet_not_found")
        return sheet_name

    def _ensure_headers(self, access_token: str, config: GoogleSheetsExportConfig) -> HeaderState:
        values = self.sheets_client.get_sheet_values(access_token=access_token, spreadsheet_id=config.spreadsheet_id, range_name=sheet_range(config.sheet_name, "A1:N1"))
        headers = [str(item) for item in values[0]] if values else []
        if not headers:
            self.sheets_client.update_sheet_values(access_token=access_token, spreadsheet_id=config.spreadsheet_id, range_name=sheet_range(config.sheet_name, "A1:N1"), values=[SHEETS_EXPORT_COLUMNS])
            return HeaderState("created", SHEETS_EXPORT_COLUMNS)
        if headers[: len(SHEETS_EXPORT_COLUMNS)] == SHEETS_EXPORT_COLUMNS:
            return HeaderState("compatible", headers)
        if headers == SHEETS_EXPORT_COLUMNS[: len(headers)]:
            missing = SHEETS_EXPORT_COLUMNS[len(headers) :]
            row = [*headers, *missing]
            self.sheets_client.update_sheet_values(access_token=access_token, spreadsheet_id=config.spreadsheet_id, range_name=sheet_range(config.sheet_name, "A1:N1"), values=[row])
            return HeaderState("extended", row)
        raise IntegrationConfigurationError("La hoja tiene encabezados incompatibles", code="google_sheets_incompatible_headers")

    def _existing_row_index(self, rows: list[list[str]]) -> dict[str, int]:
        result: dict[str, int] = {}
        for index, row in enumerate(rows[1:], start=2):
            if row:
                result[str(row[0])] = index
        return result

    def _appointments(self, starts_from: datetime, starts_to: datetime, include_cancelled: bool) -> list[Appointment]:
        query = (
            select(Appointment)
            .join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id)
            .join(ClientProfile, Appointment.client_id == ClientProfile.id)
            .where(Appointment.start_datetime >= starts_from, Appointment.start_datetime <= starts_to)
            .order_by(Appointment.start_datetime.asc(), Appointment.id.asc())
        )
        if not include_cancelled:
            query = query.where(Appointment.status != AppointmentStatus.cancelled)
        return list(self.db.scalars(query))

    def _appointment_row(self, appointment: Appointment) -> list[str]:
        professional_user = appointment.professional.user
        client_user = appointment.client.user
        meeting_url = appointment.meeting_link.meeting_url if appointment.meeting_link and appointment.meeting_link.meeting_url else appointment.meeting_url
        cancelled_at = appointment.updated_at if appointment.status == AppointmentStatus.cancelled else None
        return [
            str(appointment.id),
            appointment.status.value,
            _iso(appointment.start_datetime),
            _iso(appointment.end_datetime),
            "America/Santiago",
            _full_name(professional_user),
            professional_user.email,
            _full_name(client_user),
            client_user.email,
            appointment.meeting_provider.value if appointment.meeting_provider else "",
            meeting_url or "",
            _iso(appointment.created_at),
            _iso(appointment.updated_at),
            _iso(cancelled_at),
        ]


def _full_name(user: User) -> str:
    return f"{user.first_name} {user.last_name}".strip()


def _iso(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()
