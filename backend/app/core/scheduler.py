from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.notifications.service import AppointmentNotificationService

def _send_appointment_reminders() -> None:
    db = SessionLocal()
    try:
        AppointmentNotificationService(db).schedule_due_reminders()
    finally:
        db.close()


scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(_send_appointment_reminders, "interval", minutes=30, id="appointment-reminders", replace_existing=True)
