from datetime import datetime

from pydantic import BaseModel

from app.models.appointment import AppointmentStatus
from app.models.professional_profile import ConsultationMode
from app.schemas.common import ORMModel


class AppointmentCreate(BaseModel):
    professional_id: int
    specialty_id: int | None = None
    start_datetime: datetime
    client_notes: str | None = None


class AppointmentStatusUpdate(BaseModel):
    reason: str | None = None


class AppointmentProfessionalStatusUpdate(AppointmentStatusUpdate):
    professional_private_notes: str | None = None


class AppointmentBaseRead(ORMModel):
    id: int
    professional_id: int
    client_id: int
    category_id: int | None
    specialty_id: int | None
    start_datetime: datetime
    end_datetime: datetime
    status: AppointmentStatus
    consultation_mode: ConsultationMode
    meeting_provider: str | None
    meeting_url: str | None
    external_meeting_id: str | None
    calendar_event_id: str | None
    cancellation_reason: str | None
    client_notes: str | None


class AppointmentClientRead(AppointmentBaseRead):
    pass


class AppointmentAdminRead(AppointmentBaseRead):
    pass


class AppointmentProfessionalRead(AppointmentBaseRead):
    professional_private_notes: str | None
