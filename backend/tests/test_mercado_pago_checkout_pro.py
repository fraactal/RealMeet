from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
import hashlib
import hmac
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.models.appointment import Appointment, AppointmentExternalCalendarEvent, AppointmentHistory, AppointmentMeeting, AppointmentNotification, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.availability import AvailabilityRule
from app.models.client_profile import ClientProfile
from app.models.integration import Integration, IntegrationExecution
from app.models.payment import MercadoPagoWebhookEvent, PaymentOrder, PaymentOrderStatusHistory
from app.models.professional_profile import ConsultationMode, PaymentTiming, ProfessionalProfile
from app.models.user import User, UserRole
from app.payments.enums import PaymentOrderStatus, PaymentProviderKey
from app.payments.providers.mercado_pago import MercadoPagoHealthResult, MercadoPagoPaymentResult, MercadoPagoPreferenceResult


RUN_ID = uuid4().hex[:8]


class FakeMercadoPagoClient:
    preference_calls = 0
    payment_calls = 0
    health_calls = 0
    idempotency_keys: list[str] = []
    preference_payloads: list[dict] = []
    payment_status = "approved"
    status_detail = "accredited"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def create_preference(self, payload: dict, *, idempotency_key: str) -> MercadoPagoPreferenceResult:
        type(self).preference_calls += 1
        type(self).idempotency_keys.append(idempotency_key)
        type(self).preference_payloads.append(payload)
        order_id = payload["metadata"]["realmeet_payment_order_id"]
        return MercadoPagoPreferenceResult(
            preference_id=f"pref-{order_id}",
            init_point=f"https://www.mercadopago.cl/checkout/v1/redirect?pref_id=pref-{order_id}",
            sandbox_init_point=f"https://sandbox.mercadopago.cl/checkout/v1/redirect?pref_id=pref-{order_id}",
            status="pending",
            provider_reference={"provider": "mercado_pago", "preference_id": f"pref-{order_id}"},
        )

    def get_payment(self, payment_id: str) -> MercadoPagoPaymentResult:
        type(self).payment_calls += 1
        return MercadoPagoPaymentResult(
            payment_id=payment_id,
            status=type(self).payment_status,
            status_detail=type(self).status_detail,
            external_reference=getattr(type(self), "external_reference", None),
            preference_id=getattr(type(self), "preference_id", None),
            metadata_payment_order_id=getattr(type(self), "payment_order_id", None),
            metadata_appointment_id=getattr(type(self), "appointment_id", None),
            provider_reference={"provider": "mercado_pago", "payment_id": payment_id, "status": type(self).payment_status},
        )

    def get_preference(self, preference_id: str) -> dict:
        return {"id": preference_id, "status": "active"}

    def health_check(self) -> MercadoPagoHealthResult:
        type(self).health_calls += 1
        return MercadoPagoHealthResult(True, "mercado_pago_health_ok", "Mercado Pago fake OK.", {"account_id": "test-account"}, 1)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        user_ids = list(db.scalars(select(User.id).where(User.email.like("test-17-3-%@realmeet.local"))))
        if user_ids:
            professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.user_id.in_(user_ids))))
            client_ids = list(db.scalars(select(ClientProfile.id).where(ClientProfile.user_id.in_(user_ids))))
            appointment_ids = []
            if professional_ids:
                appointment_ids.extend(db.scalars(select(Appointment.id).where(Appointment.professional_id.in_(professional_ids))).all())
            if client_ids:
                appointment_ids.extend(db.scalars(select(Appointment.id).where(Appointment.client_id.in_(client_ids))).all())
            appointment_ids = list(set(appointment_ids))
            order_ids = list(db.scalars(select(PaymentOrder.id).where(PaymentOrder.appointment_id.in_(appointment_ids)))) if appointment_ids else []
            if order_ids:
                db.execute(delete(MercadoPagoWebhookEvent).where(MercadoPagoWebhookEvent.payment_order_id.in_(order_ids)))
                db.execute(delete(PaymentOrderStatusHistory).where(PaymentOrderStatusHistory.payment_order_id.in_(order_ids)))
                db.execute(delete(PaymentOrder).where(PaymentOrder.id.in_(order_ids)))
            if appointment_ids:
                db.execute(delete(AppointmentNotification).where(AppointmentNotification.appointment_id.in_(appointment_ids)))
                db.execute(delete(AppointmentExternalCalendarEvent).where(AppointmentExternalCalendarEvent.appointment_id.in_(appointment_ids)))
                db.execute(delete(AppointmentMeeting).where(AppointmentMeeting.appointment_id.in_(appointment_ids)))
                db.execute(delete(AppointmentHistory).where(AppointmentHistory.appointment_id.in_(appointment_ids)))
                db.execute(delete(Appointment).where(Appointment.id.in_(appointment_ids)))
            if professional_ids:
                db.execute(delete(AvailabilityRule).where(AvailabilityRule.professional_id.in_(professional_ids)))
                db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.id.in_(professional_ids)))
            if client_ids:
                db.execute(delete(ClientProfile).where(ClientProfile.id.in_(client_ids)))
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        integrations = list(db.scalars(select(Integration.id).where(Integration.name.like(f"Test 17.3 {RUN_ID}%"))))
        if integrations:
            db.execute(delete(IntegrationExecution).where(IntegrationExecution.integration_id.in_(integrations)))
            db.execute(delete(Integration).where(Integration.id.in_(integrations)))
        db.execute(delete(MercadoPagoWebhookEvent).where(MercadoPagoWebhookEvent.event_id.like(f"%{RUN_ID}%")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client(monkeypatch) -> TestClient:
    settings.rate_limit_enabled = False
    monkeypatch.setenv("MERCADO_PAGO_ACCESS_TOKEN_TEST", "TEST-token-redacted")
    monkeypatch.setenv("MERCADO_PAGO_WEBHOOK_SECRET_TEST", "webhook-secret")
    FakeMercadoPagoClient.preference_calls = 0
    FakeMercadoPagoClient.payment_calls = 0
    FakeMercadoPagoClient.health_calls = 0
    FakeMercadoPagoClient.idempotency_keys = []
    FakeMercadoPagoClient.preference_payloads = []
    FakeMercadoPagoClient.payment_status = "approved"
    FakeMercadoPagoClient.status_detail = "accredited"
    FakeMercadoPagoClient.payment_order_id = None
    FakeMercadoPagoClient.appointment_id = None
    FakeMercadoPagoClient.external_reference = None
    FakeMercadoPagoClient.preference_id = None
    monkeypatch.setattr("app.payments.service.mercado_pago_client_factory", lambda token: FakeMercadoPagoClient(token))
    monkeypatch.setattr("app.api.routes.webhooks.mercado_pago_client_factory", lambda token: FakeMercadoPagoClient(token))
    monkeypatch.setattr("app.payments.providers.mercado_pago.mercado_pago_client_factory", lambda token: FakeMercadoPagoClient(token))
    return TestClient(app)


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(email=f"test-17-3-{RUN_ID}-{suffix}-{role.value}@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Test", last_name=role.value.title(), role=role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mp_config(suffix: str = "") -> dict:
    return {
        "environment": "sandbox",
        "country": "CL",
        "currency": "CLP",
        "notification_url": f"http://localhost:18000/api/v1/webhooks/mercado-pago{suffix}",
        "success_url": "http://localhost:15173/payments/success",
        "pending_url": "http://localhost:15173/payments/pending",
        "failure_url": "http://localhost:15173/payments/failure",
        "auto_return": "approved",
        "access_token_reference": "MERCADO_PAGO_ACCESS_TOKEN_TEST",
        "webhook_secret_reference": "MERCADO_PAGO_WEBHOOK_SECRET_TEST",
    }


def _create_enabled_mp(api_client: TestClient, admin: User) -> dict:
    created = api_client.post("/api/v1/admin/integrations", headers=_headers(admin), json={"name": f"Test 17.3 {RUN_ID} MP", "integration_type": "payment", "provider": "mercado_pago", "config": _mp_config()})
    assert created.status_code == 200, created.text
    enabled = api_client.post(f"/api/v1/admin/integrations/{created.json()['id']}/enable", headers=_headers(admin))
    assert enabled.status_code == 200, enabled.text
    return enabled.json()


def _fixture(db, api_client: TestClient, *, timing: PaymentTiming = PaymentTiming.pay_before_confirmation, suffix: str = "flow"):
    admin = _user(db, UserRole.admin, f"{suffix}-admin")
    professional_user = _user(db, UserRole.professional, f"{suffix}-pro")
    client_user = _user(db, UserRole.client, f"{suffix}-client")
    _create_enabled_mp(api_client, admin)
    professional = ProfessionalProfile(user_id=professional_user.id, title=f"Test 17.3 {suffix}", consultation_mode=ConsultationMode.online, session_duration_minutes=60, price=Decimal("35000"), payment_timing=timing, payment_amount=Decimal("35000"), payment_currency="CLP", payment_expiration_minutes=30, is_public=True)
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    start = (datetime.now(UTC) + timedelta(days=5)).replace(hour=10, minute=0, second=0, microsecond=0)
    db.add(AvailabilityRule(professional_id=professional.id, weekday=start.weekday(), start_time=time(9, 0), end_time=time(12, 0), is_active=True))
    db.commit()
    return admin, professional_user, client_user, professional, client, start


def _book(api_client: TestClient, client_user: User, professional: ProfessionalProfile, start: datetime):
    return api_client.post("/api/v1/appointments", headers=_headers(client_user), json={"professional_id": professional.id, "start_datetime": start.isoformat()})


def _sign(data_id: str, request_id: str, secret: str = "webhook-secret") -> str:
    ts = "1704908010"
    digest = hmac.new(secret.encode(), f"id:{data_id};request-id:{request_id};ts:{ts};".encode(), hashlib.sha256).hexdigest()
    return f"ts={ts},v1={digest}"


def test_mercado_pago_config_permissions_and_health(api_client: TestClient, db_session) -> None:
    admin = _user(db_session, UserRole.admin, "config-admin")
    professional = _user(db_session, UserRole.professional, "config-pro")
    client = _user(db_session, UserRole.client, "config-client")
    ok = api_client.post("/api/v1/admin/integrations", headers=_headers(admin), json={"name": f"Test 17.3 {RUN_ID} config", "integration_type": "payment", "provider": "mercado_pago", "config": _mp_config()})
    token = {**_mp_config(), "access_token": "APP_USR-secret"}
    bad_token = api_client.post("/api/v1/admin/integrations", headers=_headers(admin), json={"name": f"Test 17.3 {RUN_ID} bad-token", "integration_type": "payment", "provider": "mercado_pago", "config": token})
    bad_url = {**_mp_config(), "success_url": "http://example.com/payments/success"}
    insecure = api_client.post("/api/v1/admin/integrations", headers=_headers(admin), json={"name": f"Test 17.3 {RUN_ID} bad-url", "integration_type": "payment", "provider": "mercado_pago", "config": bad_url})
    pro_forbidden = api_client.post("/api/v1/admin/integrations", headers=_headers(professional), json={"name": "x", "integration_type": "payment", "provider": "mercado_pago", "config": _mp_config()})
    client_forbidden = api_client.post("/api/v1/admin/integrations", headers=_headers(client), json={"name": "x", "integration_type": "payment", "provider": "mercado_pago", "config": _mp_config()})
    enabled = api_client.post(f"/api/v1/admin/integrations/{ok.json()['id']}/enable", headers=_headers(admin))
    health = api_client.post("/api/v1/admin/payment-providers/mercado_pago/health", headers=_headers(admin))

    assert ok.status_code == 200
    assert ok.json()["config"]["access_token_reference"] == "MERCADO_PAGO_ACCESS_TOKEN_TEST"
    assert "TEST-token" not in ok.text
    assert bad_token.status_code in {400, 422}
    assert insecure.status_code in {400, 422}
    assert pro_forbidden.status_code == 403
    assert client_forbidden.status_code == 403
    assert enabled.status_code == 200
    assert health.status_code == 200
    assert health.json()["code"] == "mercado_pago_health_ok"


def test_checkout_preference_creation_is_idempotent_and_sanitized(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, api_client, suffix="preference")
    appointment = _book(api_client, client_user, professional, start)
    order = db_session.scalar(select(PaymentOrder).where(PaymentOrder.appointment_id == appointment.json()["id"]))
    first = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/checkout", headers=_headers(client_user))
    second = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/checkout", headers=_headers(client_user))
    other = _user(db_session, UserRole.client, "other")
    db_session.add(ClientProfile(user_id=other.id))
    db_session.commit()
    forbidden = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/checkout", headers=_headers(other))

    assert appointment.status_code == 200
    assert appointment.json()["status"] == "pending_payment"
    assert order.provider == PaymentProviderKey.mercado_pago
    assert first.status_code == 200
    assert first.json()["provider"] == "mercado_pago"
    assert first.json()["checkout_url"].startswith("https://www.mercadopago.cl/")
    assert second.status_code == 200
    assert FakeMercadoPagoClient.preference_calls == 1
    assert FakeMercadoPagoClient.preference_payloads[0]["items"][0]["currency_id"] == "CLP"
    assert "client_notes" not in str(FakeMercadoPagoClient.preference_payloads[0]).lower()
    assert FakeMercadoPagoClient.idempotency_keys[0].endswith(":mercado-pago:create-preference")
    assert forbidden.status_code == 404
    assert "access_token" not in first.text.lower()


def test_webhook_signature_dedup_sync_and_reservation_policy(api_client: TestClient, db_session, monkeypatch) -> None:
    admin, _, client_user, professional, _, start = _fixture(db_session, api_client, suffix="webhook")
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = db_session.scalar(select(PaymentOrder).where(PaymentOrder.appointment_id == appointment_id))
    api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/checkout", headers=_headers(client_user))
    FakeMercadoPagoClient.payment_order_id = order.id
    FakeMercadoPagoClient.appointment_id = appointment_id
    FakeMercadoPagoClient.external_reference = f"payment-order-{order.id}"
    calls = {"count": 0}

    def count_effects(self, appointment, user):
        calls["count"] += 1

    monkeypatch.setattr("app.services.appointments.AppointmentService._run_confirmation_effects", count_effects)
    invalid = api_client.post("/api/v1/webhooks/mercado-pago?data.id=pay-1", headers={"x-signature": "ts=1,v1=bad", "x-request-id": "req-1"}, json={"id": f"evt-invalid-{RUN_ID}", "type": "payment", "data": {"id": "pay-1"}})
    valid = api_client.post("/api/v1/webhooks/mercado-pago?data.id=pay-1", headers={"x-signature": _sign("pay-1", "req-2"), "x-request-id": "req-2"}, json={"id": f"evt-valid-{RUN_ID}", "type": "payment", "data": {"id": "pay-1"}})
    duplicate = api_client.post("/api/v1/webhooks/mercado-pago?data.id=pay-1", headers={"x-signature": _sign("pay-1", "req-2"), "x-request-id": "req-2"}, json={"id": f"evt-valid-{RUN_ID}", "type": "payment", "data": {"id": "pay-1"}})
    db_session.refresh(order)

    assert invalid.json()["result"] == "invalid_signature"
    assert valid.json()["result"] == "processed"
    assert duplicate.json()["result"] == "duplicate"
    assert order.status == PaymentOrderStatus.approved
    assert db_session.get(Appointment, appointment_id).status == AppointmentStatus.confirmed
    assert FakeMercadoPagoClient.payment_calls == 1
    assert calls["count"] == 1

    FakeMercadoPagoClient.payment_status = "rejected"
    admin_sync = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/sync-provider", headers=_headers(admin))
    assert admin_sync.status_code == 200
    assert admin_sync.json()["status"] == "approved"


def test_pending_rejected_unknown_and_reconcile_paths(api_client: TestClient, db_session) -> None:
    admin, _, client_user, professional, _, start = _fixture(db_session, api_client, suffix="states")
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = db_session.scalar(select(PaymentOrder).where(PaymentOrder.appointment_id == appointment_id))
    order.external_payment_id = "pay-pending"
    db_session.commit()
    FakeMercadoPagoClient.payment_order_id = order.id
    FakeMercadoPagoClient.external_reference = f"payment-order-{order.id}"
    FakeMercadoPagoClient.payment_status = "pending"
    pending = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/sync-provider", headers=_headers(admin))
    FakeMercadoPagoClient.payment_status = "unknown_status"
    unknown = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/sync-provider", headers=_headers(admin))
    FakeMercadoPagoClient.payment_status = "rejected"
    rejected = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/sync-provider", headers=_headers(admin))

    assert pending.json()["status"] in {"draft", "pending"}
    assert unknown.json()["last_error_code"] == "payment_provider_status_unknown"
    assert rejected.json()["status"] == "rejected"
    assert db_session.get(Appointment, appointment_id).status == AppointmentStatus.cancelled

    _, _, client_user2, professional2, _, start2 = _fixture(db_session, api_client, timing=PaymentTiming.pay_after_confirmation, suffix="after")
    appointment_id2 = _book(api_client, client_user2, professional2, start2).json()["id"]
    order2 = db_session.scalar(select(PaymentOrder).where(PaymentOrder.appointment_id == appointment_id2))
    order2.external_payment_id = "pay-rejected-after"
    db_session.commit()
    FakeMercadoPagoClient.payment_order_id = order2.id
    FakeMercadoPagoClient.external_reference = f"payment-order-{order2.id}"
    FakeMercadoPagoClient.payment_status = "rejected"
    rejected_after = api_client.post(f"/api/v1/admin/payment-orders/{order2.id}/sync-provider", headers=_headers(admin))
    reconcile = api_client.post(f"/api/v1/admin/payment-orders/{order2.id}/reconcile", headers=_headers(admin))

    assert rejected_after.json()["status"] == "rejected"
    assert db_session.get(Appointment, appointment_id2).status == AppointmentStatus.confirmed
    assert reconcile.json()["result"] in {"manual_review_required", "in_sync"}
    assert "token" not in rejected_after.text.lower()
