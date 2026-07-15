import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

import app.db.base  # noqa: F401 - register all SQLAlchemy models for relationship resolution.
from app.core.security import hash_password
from app.core.config import settings
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.models.appointment import (
    Appointment,
    AppointmentNotification,
    AppointmentNotificationChannel,
    AppointmentNotificationEvent,
    AppointmentNotificationStatus,
    AppointmentStatus,
)
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.client_profile import ClientProfile
from app.models.integration import Integration, IntegrationExecution
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.models.whatsapp import WhatsAppConsent, WhatsAppMessage, WhatsAppTemplate
from app.notifications.service import AppointmentNotificationService
from app.whatsapp.cloud_client import FakeWhatsAppCloudClient
from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentSource,
    WhatsAppConsentStatus,
    WhatsAppMessageStatus,
    WhatsAppTemplateCategory,
    WhatsAppTemplatePurpose,
    WhatsAppTemplateStatus,
)
from app.whatsapp.messaging import WhatsAppMessagingService
from app.whatsapp.phone import normalize_phone, phone_hmac


class FakeMailer:
    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.sent: list[dict[str, str]] = []

    def send(self, *, subject: str, recipient: str, body: str) -> bool:
        self.sent.append({"subject": subject, "recipient": recipient, "body": body})
        return self.success


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    _cleanup(db)
    try:
        yield db
    finally:
        _cleanup(db)
        db.close()


@pytest.fixture(autouse=True)
def whatsapp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WHATSAPP_TEST_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_HMAC_KEY", "test-hmac-key")
    monkeypatch.setattr(settings, "whatsapp_phone_hmac_key", "test-hmac-key")


def test_email_only_uses_email_without_whatsapp(db_session) -> None:
    _integration(db_session, policy="email_only")
    _, appointment = _appointment_graph(db_session)
    mailer = FakeMailer()
    service = _service(db_session, mailer=mailer)

    items = service.dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    assert [item.channel for item in items] == [AppointmentNotificationChannel.email]
    assert items[0].status == AppointmentNotificationStatus.sent
    assert len(mailer.sent) == 2  # client traceable email plus professional compatibility email


def test_whatsapp_preferred_accepts_without_email_fallback(db_session) -> None:
    integration = _integration(db_session, policy="whatsapp_preferred")
    client, appointment = _appointment_graph(db_session)
    _template(db_session, integration, WhatsAppTemplatePurpose.appointment_confirmation)
    _consent(db_session, client, WhatsAppConsentPurpose.appointment_transactional)
    mailer = FakeMailer()
    fake_client = FakeWhatsAppCloudClient()

    items = _service(db_session, mailer=mailer, client=fake_client).dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    whatsapp = [item for item in items if item.channel == AppointmentNotificationChannel.whatsapp][0]
    assert whatsapp.status == AppointmentNotificationStatus.accepted, (whatsapp.error_code, whatsapp.error_message)
    assert whatsapp.whatsapp_message_id is not None
    assert len(fake_client.sent_payloads) == 1
    assert len([item for item in items if item.channel == AppointmentNotificationChannel.email]) == 0
    assert len(mailer.sent) == 1  # professional compatibility email only


def test_whatsapp_preferred_without_consent_falls_back_to_email(db_session) -> None:
    integration = _integration(db_session, policy="whatsapp_preferred")
    _, appointment = _appointment_graph(db_session)
    _template(db_session, integration, WhatsAppTemplatePurpose.appointment_confirmation)
    mailer = FakeMailer()

    items = _service(db_session, mailer=mailer).dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    whatsapp = [item for item in items if item.channel == AppointmentNotificationChannel.whatsapp][0]
    email = [item for item in items if item.channel == AppointmentNotificationChannel.email][0]
    assert whatsapp.status == AppointmentNotificationStatus.skipped
    assert whatsapp.error_code == "consent_not_granted"
    assert email.status == AppointmentNotificationStatus.fallback_sent
    assert email.fallback_used is True


def test_whatsapp_required_does_not_fallback(db_session) -> None:
    integration = _integration(db_session, policy="whatsapp_required")
    _, appointment = _appointment_graph(db_session)
    _template(db_session, integration, WhatsAppTemplatePurpose.appointment_confirmation)

    items = _service(db_session).dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    assert len(items) == 1
    assert items[0].status == AppointmentNotificationStatus.failed
    assert items[0].channel == AppointmentNotificationChannel.whatsapp
    db_session.refresh(appointment)
    assert appointment.status == AppointmentStatus.confirmed


def test_email_and_whatsapp_creates_independent_channels(db_session) -> None:
    integration = _integration(db_session, policy="email_and_whatsapp")
    client, appointment = _appointment_graph(db_session)
    _template(db_session, integration, WhatsAppTemplatePurpose.appointment_confirmation)
    _consent(db_session, client, WhatsAppConsentPurpose.appointment_transactional)

    items = _service(db_session).dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    assert {item.channel for item in items} == {AppointmentNotificationChannel.email, AppointmentNotificationChannel.whatsapp}
    assert len({item.idempotency_key for item in items}) == 2


def test_confirmation_repeated_does_not_duplicate(db_session) -> None:
    _integration(db_session, policy="email_only")
    _, appointment = _appointment_graph(db_session)
    service = _service(db_session)

    first = service.dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)
    second = service.dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    assert first[0].id == second[0].id
    assert db_session.scalar(select(WhatsAppMessage).where(WhatsAppMessage.idempotency_key == first[0].idempotency_key)) is None


def test_timeout_ambiguous_does_not_fallback_immediately(db_session) -> None:
    integration = _integration(db_session, policy="whatsapp_preferred")
    client, appointment = _appointment_graph(db_session)
    _template(db_session, integration, WhatsAppTemplatePurpose.appointment_confirmation)
    _consent(db_session, client, WhatsAppConsentPurpose.appointment_transactional)

    items = _service(db_session, client=FakeWhatsAppCloudClient(fail_code="timeout")).dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)

    assert len(items) == 1
    assert items[0].status == AppointmentNotificationStatus.processing
    assert items[0].error_code == "delivery_unknown"


def test_reminder_scheduler_is_idempotent(db_session) -> None:
    integration = _integration(db_session, policy="email_only", reminder_minutes_before=1440)
    _, appointment = _appointment_graph(db_session, starts_at=datetime.now(UTC) + timedelta(hours=23))
    service = _service(db_session)

    first = service.schedule_due_reminders(now=datetime.now(UTC))
    second = service.schedule_due_reminders(now=datetime.now(UTC))

    assert first[0].event_type == AppointmentNotificationEvent.appointment_reminder
    assert first[0].id == second[0].id
    assert integration.config["reminder_enabled"] is True


def test_webhook_status_updates_linked_notification(db_session) -> None:
    integration = _integration(db_session, policy="whatsapp_preferred")
    client, appointment = _appointment_graph(db_session)
    _template(db_session, integration, WhatsAppTemplatePurpose.appointment_confirmation)
    _consent(db_session, client, WhatsAppConsentPurpose.appointment_transactional)
    service = _service(db_session)
    notification = service.dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)[0]
    message = db_session.get(WhatsAppMessage, notification.whatsapp_message_id)

    service.sync_whatsapp_status(message.id, WhatsAppMessageStatus.delivered.value, None, None)
    db_session.refresh(notification)

    assert notification.status == AppointmentNotificationStatus.delivered


def _service(db, *, mailer: FakeMailer | None = None, client: FakeWhatsAppCloudClient | None = None) -> AppointmentNotificationService:
    return AppointmentNotificationService(
        db,
        mailer=mailer or FakeMailer(),
        whatsapp_service=WhatsAppMessagingService(db, client=client or FakeWhatsAppCloudClient()),
    )


def _appointment_graph(db, *, starts_at: datetime | None = None) -> tuple[User, Appointment]:
    suffix = uuid4().hex[:8]
    category = Category(name=f"Test 13.3 Category {suffix}", slug=f"test-13-3-category-{suffix}")
    client_user = User(email=f"test-13-3-client-{suffix}@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Client", last_name="Test", phone="+56912345678", role=UserRole.client, is_active=True)
    professional_user = User(email=f"test-13-3-pro-{suffix}@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Pro", last_name="Test", role=UserRole.professional, is_active=True)
    db.add_all([category, client_user, professional_user])
    db.flush()
    client = ClientProfile(user_id=client_user.id)
    professional = ProfessionalProfile(user_id=professional_user.id, category_id=category.id, consultation_mode=ConsultationMode.online, session_duration_minutes=60, is_public=True)
    db.add_all([client, professional])
    db.flush()
    start = starts_at or datetime.now(UTC) + timedelta(days=2)
    appointment = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        category_id=category.id,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        status=AppointmentStatus.confirmed,
        consultation_mode=ConsultationMode.online,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return client_user, appointment


def _integration(db, *, policy: str, reminder_minutes_before: int = 1440) -> Integration:
    integration = Integration(
        name=f"Test 13.3 WhatsApp {uuid4().hex[:8]}",
        integration_type=IntegrationType.messaging,
        provider=IntegrationProvider.whatsapp_cloud,
        enabled=True,
        status=IntegrationStatus.healthy,
        config={
            "waba_id": "123456789012345",
            "phone_number_id": "987654321098765",
            "display_phone_number_masked": "+56 9 **** 5678",
            "graph_api_version": "v20.0",
            "default_language": "es_CL",
            "country_code": "CL",
            "secret_references": {"access_token": "WHATSAPP_TEST_TOKEN", "phone_hmac_key": "WHATSAPP_PHONE_HMAC_KEY"},
            "notification_policy": policy,
            "fallback_channel": "email",
            "reminder_enabled": True,
            "reminder_minutes_before": reminder_minutes_before,
        },
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


def _template(db, integration: Integration, purpose: WhatsAppTemplatePurpose) -> WhatsAppTemplate:
    template = WhatsAppTemplate(
        integration_id=integration.id,
        name=f"{purpose.value}_13_3",
        language="es_CL",
        category=WhatsAppTemplateCategory.utility,
        status=WhatsAppTemplateStatus.approved,
        purpose=purpose,
        components_schema={"variables": [{"key": "client_name"}, {"key": "professional_name"}, {"key": "appointment_date"}, {"key": "appointment_time"}]},
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def _consent(db, user: User, purpose: WhatsAppConsentPurpose) -> WhatsAppConsent:
    phone = normalize_phone(user.phone or "", default_country_code="CL")
    consent = WhatsAppConsent(
        user_id=user.id,
        phone_e164=phone.e164,
        phone_hash=phone_hmac(phone.e164),
        phone_masked=phone.masked,
        status=WhatsAppConsentStatus.granted,
        purpose=purpose,
        source=WhatsAppConsentSource.self_service,
        consent_text_version="wa-transactional-v1",
        granted_at=datetime.now(UTC),
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def _cleanup(db) -> None:
    appointment_ids = list(
        db.scalars(
            select(Appointment.id)
            .join(ClientProfile, Appointment.client_id == ClientProfile.id)
            .join(User, ClientProfile.user_id == User.id)
            .where(User.email.like("test-13-3-%@realmeet.local"))
        )
    )
    if appointment_ids:
        db.execute(delete(AppointmentNotification).where(AppointmentNotification.appointment_id.in_(appointment_ids)))
        db.execute(delete(Appointment).where(Appointment.id.in_(appointment_ids)))
    user_ids = list(db.scalars(select(User.id).where(User.email.like("test-13-3-%@realmeet.local"))))
    if user_ids:
        db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
        db.execute(delete(WhatsAppConsent).where(WhatsAppConsent.user_id.in_(user_ids)))
        db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.user_id.in_(user_ids)))
        db.execute(delete(ClientProfile).where(ClientProfile.user_id.in_(user_ids)))
    integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 13.3 WhatsApp%"))))
    if integration_ids:
        db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
        db.execute(delete(IntegrationExecution).where(IntegrationExecution.integration_id.in_(integration_ids)))
        db.execute(delete(WhatsAppMessage).where(WhatsAppMessage.integration_id.in_(integration_ids)))
        db.execute(delete(WhatsAppTemplate).where(WhatsAppTemplate.integration_id.in_(integration_ids)))
        db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
    db.execute(delete(AuditLog).where(AuditLog.entity_name == "AppointmentNotification"))
    db.execute(delete(User).where(User.email.like("test-13-3-%@realmeet.local")))
    db.execute(delete(Category).where(Category.slug.like("test-13-3-category-%")))
    db.commit()
