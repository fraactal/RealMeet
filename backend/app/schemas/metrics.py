from pydantic import BaseModel


class StatusCounts(BaseModel):
    pending: int = 0
    confirmed: int = 0
    cancelled: int = 0
    completed: int = 0
    no_show: int = 0


class DashboardAppointmentRead(BaseModel):
    id: int
    start_datetime: str
    end_datetime: str
    status: str
    consultation_mode: str


class ClientDashboard(BaseModel):
    upcoming_reservations: int
    status_counts: StatusCounts
    recent_appointments: list[DashboardAppointmentRead]
    next_appointments: list[DashboardAppointmentRead]


class ProfessionalMetrics(BaseModel):
    today_reservations: int
    upcoming_reservations: int
    pending_reservations: int
    confirmed_reservations: int
    monthly_completed: int
    lifetime_completed: int
    unique_clients: int
    cancelled_reservations: int
    no_show_reservations: int
    cancellation_rate: float
    estimated_month_income: float
    status_counts: StatusCounts
    recent_appointments: list[DashboardAppointmentRead]
    next_appointments: list[DashboardAppointmentRead]
    is_public: bool
    availability_rules_count: int


class AdminMetrics(BaseModel):
    total_users: int
    active_clients: int
    active_professionals: int
    total_professionals: int
    total_clients: int
    public_professionals: int
    total_appointments: int
    pending_appointments: int
    confirmed_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_show_appointments: int
    active_categories: int
    active_specialties: int
    recent_appointments: list[DashboardAppointmentRead]
