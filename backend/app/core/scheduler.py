from apscheduler.schedulers.background import BackgroundScheduler


def _reminder_placeholder() -> None:
    return None


scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(_reminder_placeholder, "interval", minutes=30, id="reminder-placeholder", replace_existing=True)
