from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.user import UserRole
from app.meetings.base import MeetingPayload
from app.meetings.factory import get_meeting_provider
from app.models.appointment import Appointment, AppointmentHistory, AppointmentStatus
from app.models.client_profile import ClientProfile
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User
from app.notifications.service import AppointmentNotificationService
from app.automation.service import DomainEventPublisher
from app.schemas.appointments import AppointmentCreate, AppointmentPrivateNotesUpdate, AppointmentProfessionalStatusUpdate, AppointmentStatusUpdate
from app.services.availability import AvailabilityService
from app.services.appointment_calendar_sync import AppointmentCalendarSyncService
from app.services.external_availability import ExternalAvailabilityConflict, ExternalAvailabilityService, ExternalAvailabilityUnavailable
from app.integrations.google_workspace.document_automation import DocumentAutomationEventType, DocumentAutomationService


ACTIVE_STATUSES = [AppointmentStatus.pending, AppointmentStatus.confirmed]
CLIENT_CANCELABLE_STATUSES = [AppointmentStatus.pending, AppointmentStatus.confirmed]
PROFESSIONAL_TRANSITIONS = {
    AppointmentStatus.confirmed: [AppointmentStatus.pending],
    AppointmentStatus.cancelled: [AppointmentStatus.pending, AppointmentStatus.confirmed],
    AppointmentStatus.completed: [AppointmentStatus.confirmed],
    AppointmentStatus.no_show: [AppointmentStatus.confirmed],
}


class AppointmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User, payload: AppointmentCreate) -> Appointment:
        client_profile = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if not client_profile:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client profile not found")

        start_datetime = self._ensure_aware_utc(payload.start_datetime)
        if start_datetime <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment must be in the future")

        professional = self.db.scalar(
            select(ProfessionalProfile)
            .options(selectinload(ProfessionalProfile.user), selectinload(ProfessionalProfile.category))
            .where(ProfessionalProfile.id == payload.professional_id)
            .with_for_update()
        )
        if not professional:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found")
        if not professional.is_public or not professional.user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found")

        duration_minutes = self._get_duration_minutes(professional)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        self._ensure_no_active_overlap(professional.id, client_profile.id, start_datetime, end_datetime)
        self._ensure_available_slot(professional, start_datetime, end_datetime)
        self._ensure_external_available(professional.id, start_datetime, end_datetime)

        appointment = Appointment(
            professional_id=professional.id,
            client_id=client_profile.id,
            category_id=professional.category_id,
            specialty_id=payload.specialty_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            consultation_mode=professional.consultation_mode,
            client_notes=payload.client_notes,
        )
        self.db.add(appointment)
        try:
            self.db.flush()
            self._add_history(appointment.id, user.id, None, AppointmentStatus.pending.value, "Appointment created")
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected slot is already booked") from exc
        self.db.refresh(appointment)
        AppointmentCalendarSyncService(self.db).sync_created(appointment, user)
        self.db.refresh(appointment)
        AppointmentNotificationService(self.db).notify_created(appointment)
        DomainEventPublisher(self.db).publish_appointment_created(appointment)
        self._run_document_automation(DocumentAutomationEventType.appointment_created, appointment, user)
        return appointment

    def list_for_user(self, user: User) -> list[Appointment]:
        query = select(Appointment).order_by(Appointment.start_datetime.desc())
        if user.role == UserRole.client:
            query = query.join(ClientProfile, Appointment.client_id == ClientProfile.id).where(ClientProfile.user_id == user.id)
        elif user.role == UserRole.professional:
            query = query.join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id).where(
                ProfessionalProfile.user_id == user.id
            )
        return list(self.db.scalars(query))

    def get_for_actor(self, appointment_id: int, user: User) -> Appointment:
        appointment = self.db.get(Appointment, appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if user.role == UserRole.admin:
            return appointment
        if user.role == UserRole.client:
            client_profile = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
            if not client_profile or appointment.client_id != client_profile.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if user.role == UserRole.professional:
            professional = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
            if not professional or appointment.professional_id != professional.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        return appointment

    def list_history(self, appointment_id: int) -> list[AppointmentHistory]:
        return list(
            self.db.scalars(
                select(AppointmentHistory)
                .where(AppointmentHistory.appointment_id == appointment_id)
                .order_by(AppointmentHistory.created_at.asc(), AppointmentHistory.id.asc())
            )
        )

    def cancel(self, appointment: Appointment, user: User, payload: AppointmentStatusUpdate) -> Appointment:
        if user.role == UserRole.client:
            self._ensure_client_can_cancel(appointment)
        elif user.role == UserRole.professional:
            self._ensure_professional_transition(appointment, AppointmentStatus.cancelled)
        elif user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return self._set_status(appointment, user, AppointmentStatus.cancelled, payload.reason)

    def transition(
        self,
        appointment: Appointment,
        user: User,
        new_status: AppointmentStatus,
        payload: AppointmentStatusUpdate | AppointmentProfessionalStatusUpdate,
    ) -> Appointment:
        if user.role == UserRole.professional:
            self._ensure_professional_transition(appointment, new_status)
        elif user.role == UserRole.admin:
            self._ensure_admin_transition(appointment, new_status)
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        item = self._set_status(appointment, user, new_status, payload.reason)
        professional_private_notes = getattr(payload, "professional_private_notes", None)
        if user.role == UserRole.professional and professional_private_notes is not None:
            item.professional_private_notes = professional_private_notes
            self._add_history(item.id, user.id, item.status.value, item.status.value, "Private notes updated")
            self.db.commit()
            self.db.refresh(item)
        return item

    def update_private_notes(self, appointment: Appointment, user: User, payload: AppointmentPrivateNotesUpdate) -> Appointment:
        if user.role != UserRole.professional:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        appointment.professional_private_notes = payload.professional_private_notes
        self._add_history(appointment.id, user.id, appointment.status.value, appointment.status.value, "Private notes updated")
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def _set_status(self, appointment: Appointment, user: User, new_status: AppointmentStatus, reason: str | None) -> Appointment:
        old_status = appointment.status.value
        appointment.status = new_status
        if new_status == AppointmentStatus.cancelled and reason:
            appointment.cancellation_reason = reason
        self._add_history(appointment.id, user.id, old_status, new_status.value, reason or f"Status changed to {new_status.value}")
        self.db.commit()
        self.db.refresh(appointment)
        if new_status == AppointmentStatus.confirmed:
            from app.services.meeting_provisioning import MeetingProvisioningService

            MeetingProvisioningService(self.db).provision_for_appointment(appointment, user)
            self.db.refresh(appointment)
            AppointmentCalendarSyncService(self.db).sync_updated(appointment, user)
            self.db.refresh(appointment)
            AppointmentNotificationService(self.db).notify_confirmed(appointment)
            self._run_document_automation(DocumentAutomationEventType.appointment_confirmed, appointment, user)
        if new_status == AppointmentStatus.cancelled:
            from app.services.meeting_provisioning import MeetingProvisioningService

            MeetingProvisioningService(self.db).cancel_for_appointment(appointment, user)
            self.db.refresh(appointment)
            AppointmentCalendarSyncService(self.db).sync_cancelled(appointment, user)
            self.db.refresh(appointment)
            AppointmentNotificationService(self.db).notify_cancelled(appointment)
            DomainEventPublisher(self.db).publish_appointment_cancelled(appointment)
            self._run_document_automation(DocumentAutomationEventType.appointment_cancelled, appointment, user)
        return appointment

    def _run_document_automation(self, event_type: DocumentAutomationEventType, appointment: Appointment, user: User) -> None:
        try:
            DocumentAutomationService(self.db).handle_appointment_event(event_type, appointment, actor=user)
        except Exception:
            self.db.rollback()

    def _add_history(self, appointment_id: int, changed_by_user_id: int, old_status: str | None, new_status: str, comment: str) -> None:
        self.db.add(
            AppointmentHistory(
                appointment_id=appointment_id,
                changed_by_user_id=changed_by_user_id,
                old_status=old_status,
                new_status=new_status,
                comment=comment,
                created_at=datetime.now(UTC),
            )
        )

    def _ensure_no_active_overlap(self, professional_id: int, client_id: int, start_datetime: datetime, end_datetime: datetime) -> None:
        overlap = self.db.scalar(
            select(Appointment).where(
                Appointment.professional_id == professional_id,
                Appointment.start_datetime < end_datetime,
                Appointment.end_datetime > start_datetime,
                Appointment.status.in_(ACTIVE_STATUSES),
            )
        )
        if overlap:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected slot is already booked")
        client_overlap = self.db.scalar(
            select(Appointment).where(
                Appointment.client_id == client_id,
                Appointment.start_datetime < end_datetime,
                Appointment.end_datetime > start_datetime,
                Appointment.status.in_(ACTIVE_STATUSES),
            )
        )
        if client_overlap:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Client already has an active appointment at this time")

    def _ensure_available_slot(self, professional: ProfessionalProfile, start_datetime: datetime, end_datetime: datetime) -> None:
        slots = AvailabilityService(self.db).list_slots(professional, start_datetime, end_datetime, include_external=False)
        if not any(slot["start_datetime"] == start_datetime and slot["end_datetime"] == end_datetime for slot in slots):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected slot is not available")

    def _ensure_external_available(self, professional_id: int, start_datetime: datetime, end_datetime: datetime) -> None:
        try:
            ExternalAvailabilityService(self.db).validate_range(professional_id, start_datetime, end_datetime)
        except ExternalAvailabilityConflict as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "external_calendar_conflict", "message": "El horario seleccionado ya no esta disponible."},
            ) from exc
        except ExternalAvailabilityUnavailable as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "external_calendar_unavailable", "message": "No pudimos verificar la disponibilidad externa. Intenta nuevamente."},
            ) from exc

    @staticmethod
    def _create_meeting_payload(professional: ProfessionalProfile, start_datetime: datetime) -> MeetingPayload | None:
        if professional.consultation_mode.value not in {"online", "hybrid"}:
            return None
        try:
            return get_meeting_provider().create_meeting(
                professional_name=f"{professional.user.first_name} {professional.user.last_name}",
                starts_at=start_datetime,
            )
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configured meeting provider is not available",
            ) from exc

    @staticmethod
    def _ensure_client_can_cancel(appointment: Appointment) -> None:
        if appointment.status not in CLIENT_CANCELABLE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment cannot be cancelled")
        if appointment.start_datetime <= datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Past appointments cannot be cancelled")

    @staticmethod
    def _ensure_professional_transition(appointment: Appointment, new_status: AppointmentStatus) -> None:
        allowed_from = PROFESSIONAL_TRANSITIONS.get(new_status)
        if not allowed_from or appointment.status not in allowed_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid appointment status transition")

    @staticmethod
    def _ensure_admin_transition(appointment: Appointment, new_status: AppointmentStatus) -> None:
        if new_status not in PROFESSIONAL_TRANSITIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid appointment status transition")
        if appointment.status not in PROFESSIONAL_TRANSITIONS[new_status]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid appointment status transition")

    @staticmethod
    def _get_duration_minutes(professional: ProfessionalProfile) -> int:
        if professional.session_duration_minutes and professional.session_duration_minutes > 0:
            return professional.session_duration_minutes
        return 60

    @staticmethod
    def _ensure_aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
