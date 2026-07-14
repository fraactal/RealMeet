from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.client_profile import ClientProfile
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User, UserRole


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def professional_metrics(self, user: User) -> dict:
        professional = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = self.db.scalar(select(func.count(Appointment.id)).where(Appointment.professional_id == professional.id)) or 0
        cancelled = (
            self.db.scalar(
                select(func.count(Appointment.id)).where(
                    Appointment.professional_id == professional.id,
                    Appointment.status == AppointmentStatus.cancelled,
                )
            )
            or 0
        )
        monthly_completed = (
            self.db.scalar(
                select(func.count(Appointment.id)).where(
                    Appointment.professional_id == professional.id,
                    Appointment.status == AppointmentStatus.completed,
                    Appointment.start_datetime >= month_start,
                )
            )
            or 0
        )
        lifetime_completed = (
            self.db.scalar(
                select(func.count(Appointment.id)).where(
                    Appointment.professional_id == professional.id,
                    Appointment.status == AppointmentStatus.completed,
                )
            )
            or 0
        )
        unique_clients = (
            self.db.scalar(
                select(func.count(func.distinct(Appointment.client_id))).where(Appointment.professional_id == professional.id)
            )
            or 0
        )
        today = now.date()
        today_reservations = (
            self.db.scalar(
                select(func.count(Appointment.id)).where(
                    Appointment.professional_id == professional.id,
                    func.date(Appointment.start_datetime) == today,
                )
            )
            or 0
        )
        upcoming_reservations = (
            self.db.scalar(
                select(func.count(Appointment.id)).where(
                    Appointment.professional_id == professional.id,
                    Appointment.start_datetime >= now,
                )
            )
            or 0
        )
        estimated_month_income = float((professional.price or 0) * monthly_completed)
        cancellation_rate = round((cancelled / total) * 100, 2) if total else 0.0
        return {
            "today_reservations": today_reservations,
            "upcoming_reservations": upcoming_reservations,
            "monthly_completed": monthly_completed,
            "lifetime_completed": lifetime_completed,
            "unique_clients": unique_clients,
            "cancelled_reservations": cancelled,
            "cancellation_rate": cancellation_rate,
            "estimated_month_income": estimated_month_income,
        }

    def admin_metrics(self) -> dict:
        return {
            "total_users": self.db.scalar(select(func.count(User.id))) or 0,
            "total_professionals": self.db.scalar(select(func.count(User.id)).where(User.role == UserRole.professional)) or 0,
            "total_clients": self.db.scalar(select(func.count(User.id)).where(User.role == UserRole.client)) or 0,
            "total_appointments": self.db.scalar(select(func.count(Appointment.id))) or 0,
        }
