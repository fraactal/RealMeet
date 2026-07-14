import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    def send(self, subject: str, recipient: str, body: str) -> None:
        if not settings.smtp_host:
            print(f"[EMAIL-DEV] To={recipient} Subject={subject}\n{body}")
            return

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = recipient
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_user and settings.smtp_password:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)


email_service = EmailService()
