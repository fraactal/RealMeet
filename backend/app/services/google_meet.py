from datetime import UTC, datetime, timedelta
import logging
import re
import secrets
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationError, IntegrationNotFoundError, IntegrationProviderExecutionError
from app.integrations.google_calendar import CalendarEventResult, GoogleCalendarClient, GoogleCalendarHTTPClient, wait_for_conference
from app.integrations.google_oauth import GoogleOAuthClient, GoogleOAuthService
from app.integrations.meeting_contracts import MeetingAttendee, MeetingCreateRequest, MeetingResult
from app.models.audit_log import AuditLog
from app.models.integration import ExternalMeeting, Integration, IntegrationCredential, IntegrationExecution
from app.models.user import User

logger = logging.getLogger("realmeet.integrations.google_meet")

SEND_UPDATES = {"none", "all", "externalOnly"}
DEFAULT_DESCRIPTION = "Reunion programada mediante RealMeet."
DEFAULT_TIMEZONE = "America/Santiago"


class GoogleMeetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar_id: str = Field(default="primary", min_length=1, max_length=255)
    send_updates: str = "none"
    default_timezone: str = DEFAULT_TIMEZONE
    appointment_policy: str = "mock_only"
    fallback_provider: str = "mock"
    include_appointment_attendees: bool = False


class GoogleMeetService:
    def __init__(self, db: Session, *, calendar_client: GoogleCalendarClient | None = None, oauth_client: GoogleOAuthClient | None = None, app_settings: Settings | None = None, now: datetime | None = None) -> None:
        self.db = db
        self.calendar_client = calendar_client or GoogleCalendarHTTPClient()
        self.oauth_client = oauth_client
        self.settings = app_settings or settings
        self.now = now

    def health_check(self, integration: Integration, admin_user: User) -> MeetingResult:
        self._ensure_operational(integration)
        config = self._config(integration)
        access_token = self._access_token(integration, admin_user)
        started = self._now()
        execution = self._start_execution(integration, "health_check", f"google-meet:health:{integration.id}:{started.isoformat()}")
        try:
            self.calendar_client.get_calendar(access_token=access_token, calendar_id=config.calendar_id)
            result = MeetingResult(
                provider=IntegrationProvider.google_meet.value,
                external_event_id="calendar-health",
                external_calendar_id=config.calendar_id,
                meeting_url=None,
                html_link=None,
                conference_id=None,
                status="healthy",
                start_at=started,
                end_at=started,
                metadata={"operation": "health_check"},
            )
            self._finish_execution(execution, IntegrationExecutionStatus.succeeded, result)
            integration.status = IntegrationStatus.healthy
            integration.last_checked_at = self._now()
            integration.last_success_at = self._now()
            integration.last_error_message = None
            self._audit(admin_user, "google_meet_health_checked", integration, {"result": "succeeded", "operation": "health_check"})
            self.db.commit()
            return result
        except IntegrationError as exc:
            self._finish_failed(execution, exc)
            integration.status = IntegrationStatus.error
            integration.last_checked_at = self._now()
            integration.last_error_at = self._now()
            integration.last_error_message = exc.message
            self._audit(admin_user, "google_meet_health_checked", integration, {"result": "failed", "code": exc.code})
            self.db.commit()
            raise

    def create_meeting(self, integration_id: int, request: MeetingCreateRequest, admin_user: User) -> MeetingResult:
        integration = self._integration(integration_id)
        self._ensure_operational(integration)
        self._validate_request(request)
        config = self._config(integration)
        previous = self._successful_execution(integration.id, request.idempotency_key)
        if previous:
            existing = self._meeting_from_execution(previous)
            if existing:
                return self._result_from_meeting(existing, metadata={"idempotent": True})
        execution = self._start_or_retry_execution(integration, "create_meeting", request.idempotency_key, request.entity_type, request.entity_id)
        try:
            access_token = self._access_token(integration, admin_user)
            request_id = f"realmeet-{secrets.token_urlsafe(24)}"
            event = self.calendar_client.create_event(access_token=access_token, calendar_id=config.calendar_id, request=request, request_id=request_id)
            event = wait_for_conference(self.calendar_client, access_token=access_token, calendar_id=config.calendar_id, event=event)
            meeting_url = _safe_meet_url(event.hangout_link)
            if event.conference_status == "failure":
                raise IntegrationProviderExecutionError("Google no pudo crear la conferencia Meet", code="google_meet_conference_failed")
            if event.conference_status == "pending" and not meeting_url:
                raise IntegrationProviderExecutionError("La conferencia Google Meet quedo pendiente", code="google_meet_conference_pending")
            if not meeting_url:
                raise IntegrationProviderExecutionError("Google no devolvio un enlace Meet valido", code="google_meet_url_missing")
            meeting = self._upsert_external_meeting(integration, config.calendar_id, event, meeting_url, request)
            result = self._result_from_meeting(meeting, metadata={"request_id": request_id})
            self._finish_execution(execution, IntegrationExecutionStatus.succeeded, result, meeting.id)
            integration.status = IntegrationStatus.healthy
            integration.last_success_at = self._now()
            integration.last_error_message = None
            self._audit(admin_user, "google_meet_meeting_created", integration, {"result": "succeeded", "operation": "create_meeting", "external_event_id": _mask(event.event_id)})
            self.db.commit()
            self.db.refresh(meeting)
            return self._result_from_meeting(meeting)
        except IntegrationError as exc:
            self._finish_failed(execution, exc)
            integration.status = IntegrationStatus.error
            integration.last_error_at = self._now()
            integration.last_error_message = exc.message
            self._audit(admin_user, "google_meet_meeting_failed", integration, {"result": "failed", "operation": "create_meeting", "code": exc.code})
            self.db.commit()
            raise

    def get_meeting(self, integration_id: int, external_event_id: str, admin_user: User) -> MeetingResult:
        integration = self._integration(integration_id)
        meeting = self._meeting(integration.id, external_event_id)
        config = self._config(integration)
        access_token = self._access_token(integration, admin_user)
        event = self.calendar_client.get_event(access_token=access_token, calendar_id=config.calendar_id, event_id=meeting.external_event_id)
        meeting.status = "cancelled" if event.status == "cancelled" else meeting.status
        if event.hangout_link:
            meeting.meeting_url = _safe_meet_url(event.hangout_link)
        meeting.html_link = event.html_link or meeting.html_link
        self._audit(admin_user, "google_meet_meeting_read", integration, {"result": "succeeded", "operation": "get_meeting", "external_event_id": _mask(meeting.external_event_id)})
        self.db.commit()
        return self._result_from_meeting(meeting)

    def cancel_meeting(self, integration_id: int, external_event_id: str, admin_user: User, *, idempotency_key: str, send_updates: str = "none") -> MeetingResult:
        integration = self._integration(integration_id)
        meeting = self._meeting(integration.id, external_event_id)
        _validate_send_updates(send_updates)
        previous = self._successful_execution(integration.id, idempotency_key)
        if previous and meeting.status == "cancelled":
            return self._result_from_meeting(meeting, metadata={"idempotent": True})
        execution = self._start_or_retry_execution(integration, "cancel_meeting", idempotency_key, "external_meeting", str(meeting.id))
        try:
            access_token = self._access_token(integration, admin_user)
            self.calendar_client.delete_event(access_token=access_token, calendar_id=meeting.external_calendar_id, event_id=meeting.external_event_id, send_updates=send_updates)
            meeting.status = "cancelled"
            meeting.cancelled_at = self._now()
            result = self._result_from_meeting(meeting)
            self._finish_execution(execution, IntegrationExecutionStatus.succeeded, result, meeting.id)
            self._audit(admin_user, "google_meet_meeting_cancelled", integration, {"result": "succeeded", "operation": "cancel_meeting", "external_event_id": _mask(meeting.external_event_id)})
            self.db.commit()
            return result
        except IntegrationError as exc:
            self._finish_failed(execution, exc)
            self._audit(admin_user, "google_meet_meeting_failed", integration, {"result": "failed", "operation": "cancel_meeting", "code": exc.code})
            self.db.commit()
            raise

    def list_meetings(self, integration_id: int, *, limit: int = 10) -> list[ExternalMeeting]:
        integration = self._integration(integration_id)
        return list(
            self.db.scalars(
                select(ExternalMeeting)
                .where(ExternalMeeting.integration_id == integration.id, ExternalMeeting.provider == IntegrationProvider.google_meet)
                .order_by(ExternalMeeting.created_at.desc(), ExternalMeeting.id.desc())
                .limit(limit)
            )
        )

    def _integration(self, integration_id: int) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration:
            raise IntegrationNotFoundError("Integracion no encontrada", code="integration_not_found")
        if integration.provider != IntegrationProvider.google_meet:
            raise IntegrationConfigurationError("La operacion requiere una integracion Google Meet", code="google_meet_provider_required")
        return integration

    def _ensure_operational(self, integration: Integration) -> None:
        if not integration.enabled:
            raise IntegrationConfigurationError("La integracion Google Meet debe estar habilitada para crear reuniones", code="integration_disabled")
        self._active_credential(integration.id)

    def validate_enable_ready(self, integration: Integration) -> None:
        self._active_credential(integration.id)
        self._config(integration)

    def _active_credential(self, integration_id: int) -> IntegrationCredential:
        credential = self.db.scalar(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id,
                IntegrationCredential.credential_type == "google_oauth",
                IntegrationCredential.revoked_at.is_(None),
            )
        )
        if not credential:
            raise IntegrationConfigurationError("Google Meet no esta conectado por OAuth", code="google_oauth_not_connected")
        return credential

    def _access_token(self, integration: Integration, admin_user: User) -> str:
        credential = self._active_credential(integration.id)
        if credential.expires_at and credential.expires_at <= self._now() + timedelta(minutes=2):
            GoogleOAuthService(self.db, oauth_client=self.oauth_client, app_settings=self.settings).refresh(integration.id, admin_user)
            credential = self._active_credential(integration.id)
        if not credential.encrypted_access_token:
            raise IntegrationConfigurationError("La credencial Google no tiene access token", code="google_access_token_missing")
        return TokenCipher(self.settings.google_token_encryption_key).decrypt(credential.encrypted_access_token)

    def _config(self, integration: Integration) -> GoogleMeetConfig:
        try:
            config = GoogleMeetConfig.model_validate(integration.config or {})
        except ValidationError as exc:
            raise IntegrationConfigurationError("Configuracion Google Meet invalida", code="google_meet_config_invalid") from exc
        _validate_calendar_id(config.calendar_id)
        _validate_send_updates(config.send_updates)
        _validate_timezone(config.default_timezone)
        if config.appointment_policy not in {"mock_only", "google_preferred", "google_required", "disabled"}:
            raise IntegrationConfigurationError("Politica de reuniones invalida", code="google_meet_policy_invalid")
        if config.fallback_provider != "mock":
            raise IntegrationConfigurationError("Proveedor fallback invalido", code="google_meet_fallback_invalid")
        return config

    def _validate_request(self, request: MeetingCreateRequest) -> None:
        if len(request.title.strip()) < 1 or len(request.title) > 120:
            raise IntegrationConfigurationError("Titulo de reunion invalido", code="google_meet_title_invalid")
        if len(request.description) > 500:
            raise IntegrationConfigurationError("Descripcion de reunion demasiado larga", code="google_meet_description_invalid")
        if request.start_at.tzinfo is None or request.end_at.tzinfo is None:
            raise IntegrationConfigurationError("Las fechas deben incluir zona horaria", code="google_meet_datetime_naive")
        if request.start_at >= request.end_at:
            raise IntegrationConfigurationError("El inicio debe ser anterior al termino", code="google_meet_interval_invalid")
        if len(request.attendees) > 10:
            raise IntegrationConfigurationError("Demasiados asistentes", code="google_meet_attendees_limit")
        if len({attendee.email.lower() for attendee in request.attendees}) != len(request.attendees):
            raise IntegrationConfigurationError("Asistentes duplicados", code="google_meet_attendees_duplicate")
        _validate_timezone(request.timezone)
        _validate_send_updates(request.send_updates)

    def _start_execution(self, integration: Integration, operation: str, idempotency_key: str) -> IntegrationExecution:
        execution = IntegrationExecution(integration_id=integration.id, operation=operation, idempotency_key=idempotency_key, status=IntegrationExecutionStatus.running, started_at=self._now(), request_metadata={"provider": "google_meet", "operation": operation})
        self.db.add(execution)
        self.db.flush()
        return execution

    def _start_or_retry_execution(self, integration: Integration, operation: str, idempotency_key: str, entity_type: str | None, entity_id: str | None) -> IntegrationExecution:
        existing = self.db.scalar(select(IntegrationExecution).where(IntegrationExecution.integration_id == integration.id, IntegrationExecution.idempotency_key == idempotency_key))
        if existing and existing.status == IntegrationExecutionStatus.succeeded:
            return existing
        if existing:
            existing.attempt += 1
            existing.status = IntegrationExecutionStatus.running
            existing.started_at = self._now()
            existing.finished_at = None
            existing.error_code = None
            existing.error_message = None
            return existing
        execution = IntegrationExecution(integration_id=integration.id, operation=operation, entity_type=entity_type, entity_id=entity_id, idempotency_key=idempotency_key, status=IntegrationExecutionStatus.running, started_at=self._now(), request_metadata={"provider": "google_meet", "operation": operation})
        self.db.add(execution)
        self.db.flush()
        return execution

    def _successful_execution(self, integration_id: int, idempotency_key: str) -> IntegrationExecution | None:
        return self.db.scalar(select(IntegrationExecution).where(IntegrationExecution.integration_id == integration_id, IntegrationExecution.idempotency_key == idempotency_key, IntegrationExecution.status == IntegrationExecutionStatus.succeeded))

    def _meeting_from_execution(self, execution: IntegrationExecution) -> ExternalMeeting | None:
        metadata = execution.response_metadata or {}
        meeting_id = metadata.get("external_meeting_id")
        if not meeting_id:
            return None
        return self.db.get(ExternalMeeting, meeting_id)

    def _meeting(self, integration_id: int, external_event_id: str) -> ExternalMeeting:
        meeting = self.db.scalar(select(ExternalMeeting).where(ExternalMeeting.integration_id == integration_id, ExternalMeeting.external_event_id == external_event_id, ExternalMeeting.provider == IntegrationProvider.google_meet))
        if not meeting:
            raise IntegrationNotFoundError("Reunion externa no encontrada", code="external_meeting_not_found")
        return meeting

    def _upsert_external_meeting(self, integration: Integration, calendar_id: str, event: CalendarEventResult, meeting_url: str, request: MeetingCreateRequest) -> ExternalMeeting:
        meeting = self.db.scalar(select(ExternalMeeting).where(ExternalMeeting.integration_id == integration.id, ExternalMeeting.external_event_id == event.event_id, ExternalMeeting.provider == IntegrationProvider.google_meet))
        appointment_id = int(request.entity_id) if request.entity_type == "appointment" and request.entity_id and request.entity_id.isdigit() else None
        if not meeting:
            meeting = ExternalMeeting(integration_id=integration.id, provider=IntegrationProvider.google_meet, external_event_id=event.event_id, appointment_id=appointment_id, external_calendar_id=calendar_id, starts_at=event.start_at, ends_at=event.end_at)
            self.db.add(meeting)
        elif appointment_id:
            meeting.appointment_id = appointment_id
        meeting.conference_id = event.conference_id
        meeting.meeting_url = meeting_url
        meeting.html_link = _safe_google_url(event.html_link)
        meeting.status = "active" if event.status != "cancelled" else "cancelled"
        meeting.starts_at = event.start_at
        meeting.ends_at = event.end_at
        meeting.entity_type = request.entity_type
        meeting.entity_id = request.entity_id
        self.db.flush()
        return meeting

    def _finish_execution(self, execution: IntegrationExecution, status: IntegrationExecutionStatus, result: MeetingResult, external_meeting_id: int | None = None) -> None:
        execution.status = status
        execution.finished_at = self._now()
        execution.response_metadata = {
            "external_meeting_id": external_meeting_id,
            "external_event_id": result.external_event_id,
            "calendar_id": result.external_calendar_id,
            "meeting_url": result.meeting_url,
            "conference_id": result.conference_id,
            "status": result.status,
        }
        execution.error_code = None
        execution.error_message = None
        logger.info("google_meet operation=%s execution_id=%s status=%s integration_id=%s", execution.operation, execution.id, status.value, execution.integration_id)

    def _finish_failed(self, execution: IntegrationExecution, exc: IntegrationError) -> None:
        execution.status = IntegrationExecutionStatus.failed
        execution.finished_at = self._now()
        execution.error_code = exc.code
        execution.error_message = exc.message
        execution.response_metadata = {"code": exc.code}

    def _result_from_meeting(self, meeting: ExternalMeeting, metadata: dict | None = None) -> MeetingResult:
        return MeetingResult(provider=IntegrationProvider.google_meet.value, external_event_id=meeting.external_event_id, external_calendar_id=meeting.external_calendar_id, meeting_url=meeting.meeting_url, html_link=meeting.html_link, conference_id=meeting.conference_id, status=meeting.status, start_at=meeting.starts_at, end_at=meeting.ends_at, created_at=meeting.created_at, metadata=metadata or {})

    def _audit(self, admin_user: User, action: str, integration: Integration, metadata: dict) -> None:
        self.db.add(AuditLog(user_id=admin_user.id, action=action, entity_name="Integration", entity_id=str(integration.id), metadata_json={"integration_id": integration.id, "provider": "google_meet", **metadata}, created_at=self._now()))

    def _now(self) -> datetime:
        return self.now or datetime.now(UTC)


def _safe_meet_url(value: str | None) -> str | None:
    url = _safe_google_url(value)
    if not url:
        return None
    if not re.match(r"^https://meet\.google\.com/[a-z0-9-]{3,128}$", url):
        raise IntegrationProviderExecutionError("Google devolvio un enlace Meet invalido", code="google_meet_url_invalid")
    return url


def _safe_google_url(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) > 500 or not value.startswith("https://"):
        return None
    return value


def _validate_calendar_id(value: str) -> None:
    if value == "primary":
        return
    if len(value) > 255 or not re.match(r"^[A-Za-z0-9_@.\\-]+$", value):
        raise IntegrationConfigurationError("Calendar ID invalido", code="google_calendar_id_invalid")


def _validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise IntegrationConfigurationError("Zona horaria invalida", code="google_meet_timezone_invalid") from exc


def _validate_send_updates(value: str) -> None:
    if value not in SEND_UPDATES:
        raise IntegrationConfigurationError("Politica sendUpdates invalida", code="google_meet_send_updates_invalid")


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"
