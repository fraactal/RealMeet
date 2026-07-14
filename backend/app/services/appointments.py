from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.emails.service import email_service
from app.meetings.factory import get_meeting_provider
from app.models.appointment import Appointment, AppointmentHistory, AppointmentStatus
from app.models.client_profile import ClientProfile
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User
from app.schemas.appointments import AppointmentCreate, AppointmentProfessionalStatusUpdate, AppointmentStatusUpdate


class AppointmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User, payload: AppointmentCreate) -> Appointment:
        client_profile = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if not client_profile:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client profile not found")

        professional = self.db.get(ProfessionalProfile, payload.professional_id)
        if not professional:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found")

        end_datetime = payload.start_datetime + timedelta(minutes=professional.session_duration_minutes)
        overlap = self.db.scalar(
            select(Appointment).where(
                Appointment.professional_id == professional.id,
                Appointment.start_datetime < end_datetime,
                Appointment.end_datetime > payload.start_datetime,
                Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]),
            )
        )
        if overlap:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Selected slot is already booked")

        meeting_payload = None
        if professional.consultation_mode.value in {"online", "hybrid"}:
            meeting_payload = get_meeting_provider().create_meeting(
                professional_name=f"{professional.user.first_name} {professional.user.last_name}",
                starts_at=payload.start_datetime,
            )

        appointment = Appointment(
            professional_id=professional.id,
            client_id=client_profile.id,
            category_id=professional.category_id,
            specialty_id=payload.specialty_id,
            start_datetime=payload.start_datetime,
            end_datetime=end_datetime,
            consultation_mode=professional.consultation_mode,
            meeting_provider=meeting_payload.provider if meeting_payload else None,
            meeting_url=meeting_payload.url if meeting_payload else None,
            external_meeting_id=meeting_payload.external_id if meeting_payload else None,
            calendar_event_id=meeting_payload.calendar_event_id if meeting_payload else None,
            client_notes=payload.client_notes,
        )
        self.db.add(appointment)
        self.db.flush()
        self._add_history(appointment.id, user.id, None, AppointmentStatus.pending.value, "Appointment created")
        self.db.commit()
        self.db.refresh(appointment)

        email_service.send("Nueva reserva", user.email, f"Tu reserva fue creada para {appointment.start_datetime.isoformat()}")
        email_service.send(
            "Nueva reserva recibida",
            professional.user.email,
            f"Has recibido una nueva reserva para {appointment.start_datetime.isoformat()}",
        )
        return appointment

    def list_for_user(self, user: User) -> list[Appointment]:
        query = select(Appointment).order_by(Appointment.start_datetime.desc())
        if user.role.value == "client":
            query = query.join(ClientProfile, Appointment.client_id == ClientProfile.id).where(ClientProfile.user_id == user.id)
        elif user.role.value == "professional":
            query = query.join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id).where(
                ProfessionalProfile.user_id == user.id
            )
        return list(self.db.scalars(query))

    def get_for_actor(self, appointment_id: int, user: User) -> Appointment:
        appointment = self.db.get(Appointment, appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if user.role.value == "admin":
            return appointment
        if user.role.value == "client":
            client_profile = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
            if not client_profile or appointment.client_id != client_profile.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if user.role.value == "professional":
            professional = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
            if not professional or appointment.professional_id != professional.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return appointment

    def transition(
        self,
        appointment: Appointment,
        user: User,
        new_status: AppointmentStatus,
        payload: AppointmentStatusUpdate | AppointmentProfessionalStatusUpdate,
    ) -> Appointment:
        old_status = appointment.status.value
        appointment.status = new_status
        if payload.reason:
            appointment.cancellation_reason = payload.reason
        professional_private_notes = getattr(payload, "professional_private_notes", None)
        if user.role.value == "professional" and professional_private_notes is not None:
            appointment.professional_private_notes = professional_private_notes
        self._add_history(appointment.id, user.id, old_status, new_status.value, payload.reason or f"Status changed to {new_status.value}")
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

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
