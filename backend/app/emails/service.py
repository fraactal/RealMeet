import smtplib
from email.message import EmailMessage
import logging

from app.core.config import settings

logger = logging.getLogger("realmeet.email")


class EmailService:
    def send(self, subject: str, recipient: str, body: str) -> bool:
        if settings.email_mode == "log" or not settings.smtp_host:
            logger.info("email_notification_logged recipient=%s subject=%s", recipient, subject)
            logger.debug("email_notification_body recipient=%s subject=%s body=%s", recipient, subject, body)
            return True

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = recipient
        message.set_content(body)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user and settings.smtp_password:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
            logger.info("email_notification_sent recipient=%s subject=%s", recipient, subject)
            return True
        except Exception as exc:  # noqa: BLE001 - email failure must not break business flow.
            logger.warning("email_notification_failed recipient=%s subject=%s error=%s", recipient, subject, exc.__class__.__name__)
            return False


email_service = EmailService()
