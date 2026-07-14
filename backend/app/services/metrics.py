from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.availability import AvailabilityRule
from app.models.appointment import Appointment, AppointmentStatus
from app.models.category import Category
from app.models.client_profile import ClientProfile
from app.models.professional_profile import ProfessionalProfile
from app.models.specialty import Specialty
from app.models.user import User, UserRole

APPOINTMENT_STATUSES = [
    AppointmentStatus.pending,
    AppointmentStatus.confirmed,
    AppointmentStatus.cancelled,
    AppointmentStatus.completed,
    AppointmentStatus.no_show,
]


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def client_dashboard(self, user: User) -> dict:
        client = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if not client:
            return {
                "upcoming_reservations": 0,
                "status_counts": self._empty_status_counts(),
                "recent_appointments": [],
                "next_appointments": [],
            }
        now = datetime.now(UTC)
        return {
            "upcoming_reservations": self._count(Appointment,
                Appointment.client_id == client.id,
                Appointment.start_datetime >= now,
                Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]),
            ),
            "status_counts": self._status_counts(Appointment.client_id == client.id),
            "recent_appointments": self._appointment_cards(
                select(Appointment)
                .where(Appointment.client_id == client.id)
                .order_by(Appointment.start_datetime.desc())
                .limit(5)
            ),
            "next_appointments": self._appointment_cards(
                select(Appointment)
                .where(
                    Appointment.client_id == client.id,
                    Appointment.start_datetime >= now,
                    Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]),
                )
                .order_by(Appointment.start_datetime.asc())
                .limit(5)
            ),
        }

    def professional_metrics(self, user: User) -> dict:
        professional = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        if not professional:
            return {
                "today_reservations": 0,
                "upcoming_reservations": 0,
                "pending_reservations": 0,
                "confirmed_reservations": 0,
                "monthly_completed": 0,
                "lifetime_completed": 0,
                "unique_clients": 0,
                "cancelled_reservations": 0,
                "no_show_reservations": 0,
                "cancellation_rate": 0.0,
                "estimated_month_income": 0.0,
                "status_counts": self._empty_status_counts(),
                "recent_appointments": [],
                "next_appointments": [],
                "is_public": False,
                "availability_rules_count": 0,
            }
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
            "pending_reservations": self._count(Appointment, Appointment.professional_id == professional.id, Appointment.status == AppointmentStatus.pending),
            "confirmed_reservations": self._count(Appointment, Appointment.professional_id == professional.id, Appointment.status == AppointmentStatus.confirmed),
            "monthly_completed": monthly_completed,
            "lifetime_completed": lifetime_completed,
            "unique_clients": unique_clients,
            "cancelled_reservations": cancelled,
            "no_show_reservations": self._count(Appointment, Appointment.professional_id == professional.id, Appointment.status == AppointmentStatus.no_show),
            "cancellation_rate": cancellation_rate,
            "estimated_month_income": estimated_month_income,
            "status_counts": self._status_counts(Appointment.professional_id == professional.id),
            "recent_appointments": self._appointment_cards(
                select(Appointment)
                .where(Appointment.professional_id == professional.id)
                .order_by(Appointment.start_datetime.desc())
                .limit(5)
            ),
            "next_appointments": self._appointment_cards(
                select(Appointment)
                .where(
                    Appointment.professional_id == professional.id,
                    Appointment.start_datetime >= now,
                    Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]),
                )
                .order_by(Appointment.start_datetime.asc())
                .limit(5)
            ),
            "is_public": professional.is_public,
            "availability_rules_count": self._count(AvailabilityRule, AvailabilityRule.professional_id == professional.id, AvailabilityRule.is_active.is_(True)),
        }

    def admin_metrics(self) -> dict:
        return {
            "total_users": self.db.scalar(select(func.count(User.id))) or 0,
            "active_clients": self._count(User, User.role == UserRole.client, User.is_active.is_(True)),
            "active_professionals": self._count(User, User.role == UserRole.professional, User.is_active.is_(True)),
            "total_professionals": self.db.scalar(select(func.count(User.id)).where(User.role == UserRole.professional)) or 0,
            "total_clients": self.db.scalar(select(func.count(User.id)).where(User.role == UserRole.client)) or 0,
            "public_professionals": self._count(ProfessionalProfile, ProfessionalProfile.is_public.is_(True)),
            "total_appointments": self.db.scalar(select(func.count(Appointment.id))) or 0,
            "pending_appointments": self._count(Appointment, Appointment.status == AppointmentStatus.pending),
            "confirmed_appointments": self._count(Appointment, Appointment.status == AppointmentStatus.confirmed),
            "completed_appointments": self._count(Appointment, Appointment.status == AppointmentStatus.completed),
            "cancelled_appointments": self._count(Appointment, Appointment.status == AppointmentStatus.cancelled),
            "no_show_appointments": self._count(Appointment, Appointment.status == AppointmentStatus.no_show),
            "active_categories": self._count(Category, Category.is_active.is_(True)),
            "active_specialties": self._count(Specialty, Specialty.is_active.is_(True)),
            "recent_appointments": self._appointment_cards(select(Appointment).order_by(Appointment.start_datetime.desc()).limit(5)),
        }

    def _count(self, model, *conditions) -> int:
        query = select(func.count()).select_from(model)
        if conditions:
            query = query.where(*conditions)
        return self.db.scalar(query) or 0

    def _status_counts(self, *conditions) -> dict:
        counts = self._empty_status_counts()
        for item in self.db.execute(
            select(Appointment.status, func.count(Appointment.id)).where(*conditions).group_by(Appointment.status)
        ):
            counts[item[0].value] = item[1]
        return counts

    @staticmethod
    def _empty_status_counts() -> dict:
        return {status.value: 0 for status in APPOINTMENT_STATUSES}

    def _appointment_cards(self, query) -> list[dict]:
        return [
            {
                "id": item.id,
                "start_datetime": item.start_datetime.isoformat(),
                "end_datetime": item.end_datetime.isoformat(),
                "status": item.status.value,
                "consultation_mode": item.consultation_mode.value,
            }
            for item in self.db.scalars(query)
        ]
