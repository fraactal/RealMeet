from collections.abc import Iterator
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.appointment import (
    Appointment,
    AppointmentExternalCalendarEvent,
    AppointmentHistory,
    AppointmentMeeting,
    AppointmentNotification,
    AppointmentStatus,
)
from app.models.audit_log import AuditLog
from app.models.availability import AvailabilityRule
from app.models.client_profile import ClientProfile
from app.models.payment import PaymentOrder, PaymentOrderStatusHistory
from app.models.professional_profile import ConsultationMode, PaymentTiming, ProfessionalProfile
from app.models.user import User, UserRole
from app.payments.enums import PaymentOrderStatus
from app.services.availability import AvailabilityService


RUN_ID = uuid4().hex[:8]


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        user_ids = list(db.scalars(select(User.id).where(User.email.like("test-17-2-%@realmeet.local"))))
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
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "PaymentOrder"))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    settings.rate_limit_enabled = False
    return TestClient(app)


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-17-2-{RUN_ID}-{suffix}-{role.value}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name=role.value.title(),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _start() -> datetime:
    base = datetime.now(UTC) + timedelta(days=4)
    return base.replace(hour=10, minute=0, second=0, microsecond=0)


def _fixture(db, suffix: str, timing: PaymentTiming = PaymentTiming.no_payment, *, amount: Decimal | None = Decimal("35000")):
    admin = _user(db, UserRole.admin, f"{suffix}-admin")
    professional_user = _user(db, UserRole.professional, f"{suffix}-pro")
    client_user = _user(db, UserRole.client, f"{suffix}-client")
    professional = ProfessionalProfile(
        user_id=professional_user.id,
        title=f"Test 17.2 {suffix}",
        consultation_mode=ConsultationMode.online,
        session_duration_minutes=60,
        price=amount,
        payment_timing=timing,
        payment_amount=amount,
        payment_currency="CLP",
        payment_expiration_minutes=30,
        is_public=True,
    )
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    start = _start()
    db.add(AvailabilityRule(professional_id=professional.id, weekday=start.weekday(), start_time=time(9, 0), end_time=time(12, 0), is_active=True))
    db.commit()
    return admin, professional_user, client_user, professional, client, start


def _book(api_client: TestClient, client_user: User, professional: ProfessionalProfile, start: datetime):
    return api_client.post(
        "/api/v1/appointments",
        headers=_headers(client_user),
        json={"professional_id": professional.id, "start_datetime": start.isoformat(), "client_notes": "Test 17.2 booking"},
    )


def _order_for(db, appointment_id: int) -> PaymentOrder:
    return db.scalar(select(PaymentOrder).where(PaymentOrder.appointment_id == appointment_id).order_by(PaymentOrder.id.desc()))


def test_no_payment_default_and_flow_unchanged(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "no-payment")
    response = _book(api_client, client_user, professional, start)

    assert professional.payment_timing == PaymentTiming.no_payment
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["payment"] is None
    assert _order_for(db_session, response.json()["id"]) is None


def test_pay_before_confirmation_creates_pending_payment_order_and_blocks_slot(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "before", PaymentTiming.pay_before_confirmation)
    response = _book(api_client, client_user, professional, start)
    order = _order_for(db_session, response.json()["id"])
    slots = AvailabilityService(db_session).list_slots(professional, start, start + timedelta(hours=1), include_external=False)

    assert response.status_code == 200
    assert response.json()["status"] == "pending_payment"
    assert response.json()["payment"]["order_id"] == order.id
    assert order.status == PaymentOrderStatus.draft
    assert slots == []


def test_checkout_approval_confirms_once(api_client: TestClient, db_session, monkeypatch) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "approve", PaymentTiming.pay_before_confirmation)
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = _order_for(db_session, appointment_id)
    calls = {"count": 0}

    def count_effects(self, appointment, user):
        calls["count"] += 1

    monkeypatch.setattr("app.services.appointments.AppointmentService._run_confirmation_effects", count_effects)
    first = api_client.post(f"/api/v1/clients/me/payment-orders/{order.id}/checkout/approve", headers=_headers(client_user))
    second = api_client.post(f"/api/v1/clients/me/payment-orders/{order.id}/checkout/approve", headers=_headers(client_user))
    db_session.refresh(order)
    appointment = db_session.get(Appointment, appointment_id)

    assert first.status_code == 200
    assert second.status_code == 200
    assert order.status == PaymentOrderStatus.approved
    assert appointment.status == AppointmentStatus.confirmed
    assert calls["count"] == 1


def test_reject_and_expire_cancel_pending_payment_and_release_slot(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "reject", PaymentTiming.pay_before_confirmation)
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = _order_for(db_session, appointment_id)
    rejected = api_client.post(f"/api/v1/clients/me/payment-orders/{order.id}/checkout/reject", headers=_headers(client_user))
    slots = AvailabilityService(db_session).list_slots(professional, start, start + timedelta(hours=1), include_external=False)

    assert rejected.status_code == 200
    assert db_session.get(Appointment, appointment_id).status == AppointmentStatus.cancelled
    assert len(slots) == 1

    _, _, client_user2, professional2, _, start2 = _fixture(db_session, "expire", PaymentTiming.pay_before_confirmation)
    appointment_id2 = _book(api_client, client_user2, professional2, start2).json()["id"]
    order2 = _order_for(db_session, appointment_id2)
    expired = api_client.post(f"/api/v1/admin/payment-orders/{order2.id}/fake/expire", headers=_headers(_user(db_session, UserRole.admin, "expire-actor")))

    assert expired.status_code == 200
    assert db_session.get(Appointment, appointment_id2).status == AppointmentStatus.cancelled
    assert api_client.post(f"/api/v1/admin/payment-orders/{order2.id}/fake/expire", headers=_headers(_user(db_session, UserRole.admin, "expire-actor-2"))).status_code == 200


def test_pay_after_confirmation_confirms_immediately_and_reject_does_not_cancel(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "after", PaymentTiming.pay_after_confirmation)
    response = _book(api_client, client_user, professional, start)
    order = _order_for(db_session, response.json()["id"])
    rejected = api_client.post(f"/api/v1/clients/me/payment-orders/{order.id}/checkout/reject", headers=_headers(client_user))

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert order is not None
    assert rejected.status_code == 200
    assert db_session.get(Appointment, response.json()["id"]).status == AppointmentStatus.confirmed


def test_checkout_access_provider_and_amount_are_protected(api_client: TestClient, db_session) -> None:
    admin, _, client_user, professional, client, start = _fixture(db_session, "checkout", PaymentTiming.pay_before_confirmation)
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = _order_for(db_session, appointment_id)
    other = _user(db_session, UserRole.client, "other")
    db_session.add(ClientProfile(user_id=other.id))
    db_session.commit()
    forbidden = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/checkout", headers=_headers(other))
    with_amount = api_client.post(f"/api/v1/clients/me/payment-orders/{order.id}/checkout/approve", headers=_headers(client_user), json={"amount": "1"})

    stripe = api_client.post(
        "/api/v1/admin/payment-orders",
        headers=_headers(admin),
        json={"client_id": client.id, "professional_id": professional.id, "provider": "stripe", "amount": "35000", "currency": "CLP"},
    ).json()
    stripe_checkout = api_client.get(f"/api/v1/clients/me/payment-orders/{stripe['id']}/checkout", headers=_headers(client_user))

    assert forbidden.status_code == 404
    assert with_amount.status_code == 422
    db_session.refresh(order)
    assert order.amount == Decimal("35000.00")
    assert stripe_checkout.status_code == 409


def test_expired_order_cannot_be_approved(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "expired", PaymentTiming.pay_before_confirmation)
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = _order_for(db_session, appointment_id)
    order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()
    response = api_client.post(f"/api/v1/clients/me/payment-orders/{order.id}/checkout/approve", headers=_headers(client_user))

    assert response.status_code == 409
    db_session.refresh(order)
    assert order.status == PaymentOrderStatus.expired


def test_double_booking_same_slot_does_not_duplicate_order(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "double", PaymentTiming.pay_before_confirmation)
    first = _book(api_client, client_user, professional, start)
    second = _book(api_client, client_user, professional, start)
    orders = list(db_session.scalars(select(PaymentOrder).where(PaymentOrder.professional_id == professional.id)))

    assert first.status_code == 200
    assert second.status_code == 409
    assert len(orders) == 1


def test_missing_payment_amount_does_not_leave_pending_appointment(api_client: TestClient, db_session) -> None:
    _, _, client_user, professional, _, start = _fixture(db_session, "missing-amount", PaymentTiming.pay_before_confirmation, amount=None)
    response = _book(api_client, client_user, professional, start)
    appointments = list(db_session.scalars(select(Appointment).where(Appointment.professional_id == professional.id)))

    assert response.status_code == 422
    assert appointments == []


def test_admin_configures_policy_and_invalid_values_are_rejected(api_client: TestClient, db_session) -> None:
    admin, _, _, professional, _, _ = _fixture(db_session, "admin-policy")
    updated = api_client.patch(
        f"/api/v1/admin/professionals/{professional.id}",
        headers=_headers(admin),
        json={"payment_timing": "pay_before_confirmation", "payment_amount": "45000", "payment_currency": "CLP", "payment_expiration_minutes": 45},
    )
    bad_amount = api_client.patch(f"/api/v1/admin/professionals/{professional.id}", headers=_headers(admin), json={"payment_amount": "45000.50"})
    bad_expiration = api_client.patch(f"/api/v1/admin/professionals/{professional.id}", headers=_headers(admin), json={"payment_expiration_minutes": 2})

    assert updated.status_code == 200
    assert updated.json()["payment_timing"] == "pay_before_confirmation"
    assert bad_amount.status_code == 422
    assert bad_expiration.status_code == 422


def test_reconcile_corrects_safe_states_and_does_not_reactivate_cancelled(api_client: TestClient, db_session) -> None:
    admin, _, client_user, professional, _, start = _fixture(db_session, "reconcile", PaymentTiming.pay_before_confirmation)
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = _order_for(db_session, appointment_id)
    order.status = PaymentOrderStatus.approved
    db_session.commit()
    result = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/reconcile", headers=_headers(admin))

    assert result.status_code == 200
    assert result.json()["result"] == "appointment_confirmation_required"
    assert db_session.get(Appointment, appointment_id).status == AppointmentStatus.confirmed

    _, _, client_user2, professional2, _, start2 = _fixture(db_session, "reconcile-cancel", PaymentTiming.pay_before_confirmation)
    appointment_id2 = _book(api_client, client_user2, professional2, start2).json()["id"]
    order2 = _order_for(db_session, appointment_id2)
    order2.status = PaymentOrderStatus.rejected
    db_session.commit()
    result2 = api_client.post(f"/api/v1/admin/payment-orders/{order2.id}/reconcile", headers=_headers(admin))
    result3 = api_client.post(f"/api/v1/admin/payment-orders/{order2.id}/reconcile", headers=_headers(admin))

    assert result2.json()["result"] == "appointment_cancellation_required"
    assert db_session.get(Appointment, appointment_id2).status == AppointmentStatus.cancelled
    assert result3.json()["result"] == "manual_review_required"


def test_professional_reads_status_and_responses_are_sanitized(api_client: TestClient, db_session) -> None:
    _, professional_user, client_user, professional, _, start = _fixture(db_session, "safe", PaymentTiming.pay_before_confirmation)
    appointment_id = _book(api_client, client_user, professional, start).json()["id"]
    order = _order_for(db_session, appointment_id)
    pro_list = api_client.get("/api/v1/professionals/me/payment-orders", headers=_headers(professional_user))
    client_checkout = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/checkout", headers=_headers(client_user))
    logs = list(db_session.scalars(select(AuditLog).where(AuditLog.entity_name == "PaymentOrder")))

    assert pro_list.status_code == 200
    assert pro_list.json()[0]["status"] == "draft"
    body = (pro_list.text + client_checkout.text).lower()
    for forbidden in ("card", "cvv", "secret", "request_fingerprint", "idempotency"):
        assert forbidden not in body
    assert any((log.metadata_json or {}).get("event_type") == "payment.order.created" for log in logs)
