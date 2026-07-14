import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.emails.service import EmailService, email_service
from app.models.appointment import Appointment, AppointmentStatus
from app.models.client_profile import ClientProfile
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User

logger = logging.getLogger("realmeet.notifications")


@dataclass
class AppointmentNotificationContext:
    client: User
    professional: User
    professional_name: str
    client_name: str


class AppointmentNotificationService:
    def __init__(self, db: Session, mailer: EmailService = email_service) -> None:
        self.db = db
        self.mailer = mailer

    def notify_created(self, appointment: Appointment) -> None:
        try:
            self._notify_event(
                appointment=appointment,
                subject="Reserva creada en RealMeet",
                event_label="Reserva creada",
                include_meeting=False,
                recipients=("client", "professional"),
            )
        except Exception as exc:  # noqa: BLE001 - notifications must not break appointments.
            logger.warning("appointment_notification_unhandled event=created appointment_id=%s error=%s", appointment.id, exc.__class__.__name__)

    def notify_confirmed(self, appointment: Appointment) -> None:
        try:
            self._notify_event(
                appointment=appointment,
                subject="Reserva confirmada en RealMeet",
                event_label="Reserva confirmada",
                include_meeting=True,
                recipients=("client", "professional"),
            )
        except Exception as exc:  # noqa: BLE001 - notifications must not break appointments.
            logger.warning("appointment_notification_unhandled event=confirmed appointment_id=%s error=%s", appointment.id, exc.__class__.__name__)

    def notify_cancelled(self, appointment: Appointment) -> None:
        try:
            self._notify_event(
                appointment=appointment,
                subject="Reserva cancelada en RealMeet",
                event_label="Reserva cancelada",
                include_meeting=False,
                recipients=("client", "professional"),
            )
        except Exception as exc:  # noqa: BLE001 - notifications must not break appointments.
            logger.warning("appointment_notification_unhandled event=cancelled appointment_id=%s error=%s", appointment.id, exc.__class__.__name__)

    def _notify_event(
        self,
        appointment: Appointment,
        subject: str,
        event_label: str,
        include_meeting: bool,
        recipients: tuple[str, ...],
    ) -> None:
        context = self._get_context(appointment)
        if not context:
            logger.warning("appointment_notification_context_missing appointment_id=%s event=%s", appointment.id, event_label)
            return

        recipient_map = {
            "client": context.client,
            "professional": context.professional,
        }
        for recipient_key in recipients:
            recipient = recipient_map[recipient_key]
            body = self._build_body(appointment, context, event_label, include_meeting)
            sent = self.mailer.send(subject=subject, recipient=recipient.email, body=body)
            logger.info(
                "appointment_notification_attempt appointment_id=%s event=%s recipient_role=%s sent=%s",
                appointment.id,
                event_label,
                recipient_key,
                sent,
            )

    def _get_context(self, appointment: Appointment) -> AppointmentNotificationContext | None:
        client = self.db.scalar(
            select(User)
            .join(ClientProfile, ClientProfile.user_id == User.id)
            .where(ClientProfile.id == appointment.client_id)
        )
        professional = self.db.scalar(
            select(User)
            .join(ProfessionalProfile, ProfessionalProfile.user_id == User.id)
            .where(ProfessionalProfile.id == appointment.professional_id)
        )
        if not client or not professional:
            return None
        return AppointmentNotificationContext(
            client=client,
            professional=professional,
            professional_name=f"{professional.first_name} {professional.last_name}",
            client_name=f"{client.first_name} {client.last_name}",
        )

    @staticmethod
    def _build_body(
        appointment: Appointment,
        context: AppointmentNotificationContext,
        event_label: str,
        include_meeting: bool,
    ) -> str:
        lines = [
            event_label,
            "",
            f"Reserva #{appointment.id}",
            f"Profesional: {context.professional_name}",
            f"Cliente: {context.client_name}",
            f"Inicio: {appointment.start_datetime.isoformat()}",
            f"Termino: {appointment.end_datetime.isoformat()}",
            f"Modalidad: {appointment.consultation_mode.value}",
            f"Estado: {appointment.status.value}",
        ]
        if appointment.status == AppointmentStatus.cancelled and appointment.cancellation_reason:
            lines.append(f"Motivo de cancelacion: {appointment.cancellation_reason}")
        if include_meeting and appointment.meeting_url and appointment.status != AppointmentStatus.cancelled:
            lines.extend(["", "Reunion de demostracion:", appointment.meeting_url])
        return "\n".join(lines)
