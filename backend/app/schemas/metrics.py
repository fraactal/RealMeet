from pydantic import BaseModel


class ProfessionalMetrics(BaseModel):
    today_reservations: int
    upcoming_reservations: int
    monthly_completed: int
    lifetime_completed: int
    unique_clients: int
    cancelled_reservations: int
    cancellation_rate: float
    estimated_month_income: float


class AdminMetrics(BaseModel):
    total_users: int
    total_professionals: int
    total_clients: int
    total_appointments: int
