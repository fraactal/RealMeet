from datetime import datetime

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentStatus
from app.models.professional_profile import ConsultationMode
from app.schemas.common import ORMModel


class AppointmentCreate(BaseModel):
    professional_id: int
    specialty_id: int | None = None
    start_datetime: datetime
    client_notes: str | None = Field(default=None, max_length=2000)


class AppointmentStatusUpdate(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class AppointmentProfessionalStatusUpdate(AppointmentStatusUpdate):
    professional_private_notes: str | None = Field(default=None, max_length=5000)


class AppointmentPrivateNotesUpdate(BaseModel):
    professional_private_notes: str | None = Field(default=None, max_length=5000)


class AppointmentHistoryRead(ORMModel):
    id: int
    appointment_id: int
    changed_by_user_id: int
    old_status: str | None
    new_status: str
    comment: str | None
    created_at: datetime


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
    history: list[AppointmentHistoryRead] = Field(default_factory=list)


class AppointmentClientRead(AppointmentBaseRead):
    pass


class AppointmentAdminRead(AppointmentBaseRead):
    pass


class AppointmentProfessionalRead(AppointmentBaseRead):
    professional_private_notes: str | None
