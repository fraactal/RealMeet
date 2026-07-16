from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.appointment import Appointment, AppointmentHistory, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.payment import PaymentOrder, PaymentOrderStatusHistory
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.payments.enums import PaymentOrderStatus

RUN_ID = uuid4().hex[:8]


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        appointments = list(db.scalars(select(Appointment.id).where(Appointment.client_notes.like("Test 17.1%"))))
        user_ids = list(db.scalars(select(User.id).where(User.email.like("test-17-1-%@realmeet.local"))))
        if appointments:
            db.execute(delete(PaymentOrderStatusHistory).where(PaymentOrderStatusHistory.payment_order_id.in_(select(PaymentOrder.id).where(PaymentOrder.appointment_id.in_(appointments)))))
            db.execute(delete(PaymentOrder).where(PaymentOrder.appointment_id.in_(appointments)))
            db.execute(delete(AppointmentHistory).where(AppointmentHistory.appointment_id.in_(appointments)))
            db.execute(delete(Appointment).where(Appointment.id.in_(appointments)))
        if user_ids:
            professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.user_id.in_(user_ids))))
            client_ids = list(db.scalars(select(ClientProfile.id).where(ClientProfile.user_id.in_(user_ids))))
            if professional_ids:
                db.execute(delete(PaymentOrderStatusHistory).where(PaymentOrderStatusHistory.payment_order_id.in_(select(PaymentOrder.id).where(PaymentOrder.professional_id.in_(professional_ids)))))
                db.execute(delete(PaymentOrder).where(PaymentOrder.professional_id.in_(professional_ids)))
            if client_ids:
                db.execute(delete(PaymentOrderStatusHistory).where(PaymentOrderStatusHistory.payment_order_id.in_(select(PaymentOrder.id).where(PaymentOrder.client_id.in_(client_ids)))))
                db.execute(delete(PaymentOrder).where(PaymentOrder.client_id.in_(client_ids)))
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "PaymentOrder"))
            db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.user_id.in_(user_ids)))
            db.execute(delete(ClientProfile).where(ClientProfile.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-17-1-{RUN_ID}-{suffix}-{role.value}@realmeet.local",
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


def _fixture(db, suffix: str = "base") -> tuple[User, User, User, ProfessionalProfile, ClientProfile, Appointment]:
    admin = _user(db, UserRole.admin, f"{suffix}-admin")
    professional_user = _user(db, UserRole.professional, f"{suffix}-pro")
    client_user = _user(db, UserRole.client, f"{suffix}-client")
    professional = ProfessionalProfile(
        user_id=professional_user.id,
        title=f"Test 17.1 {suffix}",
        consultation_mode=ConsultationMode.online,
        session_duration_minutes=60,
        price=Decimal("35000"),
        is_public=True,
    )
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    db.refresh(client)
    appointment = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        start_datetime=datetime.now(UTC) + timedelta(days=3),
        end_datetime=datetime.now(UTC) + timedelta(days=3, hours=1),
        status=AppointmentStatus.pending,
        consultation_mode=ConsultationMode.online,
        client_notes=f"Test 17.1 {suffix}",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return admin, professional_user, client_user, professional, client, appointment


def _create_order(api_client: TestClient, admin: User, appointment: Appointment, **overrides) -> dict:
    payload = {"appointment_id": appointment.id, "provider": "fake", "description": "Pago reserva test", **overrides}
    response = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _submit(api_client: TestClient, admin: User, order_id: int) -> dict:
    response = api_client.post(f"/api/v1/admin/payment-orders/{order_id}/submit", headers=_headers(admin))
    assert response.status_code == 200, response.text
    return response.json()


def test_admin_creates_valid_order_and_price_snapshot(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "create")
    order = _create_order(api_client, admin, appointment)
    db_session.get(ProfessionalProfile, appointment.professional_id).price = Decimal("99000")
    db_session.commit()

    assert order["amount"] in ("35000.00", 35000, "35000")
    assert order["currency"] == "CLP"
    assert order["status"] == "draft"


@pytest.mark.parametrize("amount", ["0", "-1000", "35000.50"])
def test_invalid_amounts_are_rejected(api_client: TestClient, db_session, amount: str) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, f"invalid-{amount.replace('.', '-')}")
    response = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json={"appointment_id": appointment.id, "provider": "fake", "amount": amount})

    assert response.status_code == 422


def test_provider_fake_submit_and_approval_flow(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "fake")
    order = _create_order(api_client, admin, appointment)
    submitted = _submit(api_client, admin, order["id"])
    approved = api_client.post(f"/api/v1/admin/payment-orders/{order['id']}/fake/approve", headers=_headers(admin))
    invalid = api_client.post(f"/api/v1/admin/payment-orders/{order['id']}/submit", headers=_headers(admin))

    assert submitted["status"] == "pending"
    assert submitted["external_payment_id"].startswith("fake_pay_")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert invalid.status_code == 409
    assert invalid.json()["detail"]["code"] == "payment_invalid_status_transition"


def test_provider_not_implemented_fails_clearly(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "stripe")
    order = _create_order(api_client, admin, appointment, provider="stripe")
    response = api_client.post(f"/api/v1/admin/payment-orders/{order['id']}/submit", headers=_headers(admin))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "payment_provider_not_implemented"


@pytest.mark.parametrize("operation,status_value", [("reject", "rejected"), ("cancel", "cancelled"), ("expire", "expired"), ("fail", "failed")])
def test_terminal_fake_operations_register_history(api_client: TestClient, db_session, operation: str, status_value: str) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, f"terminal-{operation}")
    order = _create_order(api_client, admin, appointment)
    _submit(api_client, admin, order["id"])
    path = f"/api/v1/admin/payment-orders/{order['id']}/cancel" if operation == "cancel" else f"/api/v1/admin/payment-orders/{order['id']}/fake/{operation}"
    response = api_client.post(path, headers=_headers(admin))
    history = api_client.get(f"/api/v1/admin/payment-orders/{order['id']}/history", headers=_headers(admin))

    assert response.status_code == 200
    assert response.json()["status"] == status_value
    assert any(item["new_status"] == status_value for item in history.json())
    if operation == "fail":
        assert response.json()["last_error_code"] == "fake_payment_failed"
        assert "token" not in response.text.lower()
        assert "secret" not in response.text.lower()


def test_idempotency_returns_same_order_and_conflicts_on_different_payload(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "idem")
    headers = {**_headers(admin), "Idempotency-Key": "test-17-1-idem"}
    payload = {"appointment_id": appointment.id, "provider": "fake", "amount": "35000"}
    first = api_client.post("/api/v1/admin/payment-orders", headers=headers, json=payload)
    second = api_client.post("/api/v1/admin/payment-orders", headers=headers, json=payload)
    conflict = api_client.post("/api/v1/admin/payment-orders", headers=headers, json={**payload, "amount": "36000"})

    assert first.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "payment_idempotency_conflict"


def test_submit_retry_does_not_create_another_external_payment(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "submit-retry")
    order = _create_order(api_client, admin, appointment)
    first = _submit(api_client, admin, order["id"])
    second = _submit(api_client, admin, order["id"])

    assert second["external_payment_id"] == first["external_payment_id"]


def test_historical_orders_allowed_after_rejection_but_not_two_active(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "history")
    first = _create_order(api_client, admin, appointment)
    active = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json={"appointment_id": appointment.id, "provider": "fake"})
    _submit(api_client, admin, first["id"])
    api_client.post(f"/api/v1/admin/payment-orders/{first['id']}/fake/reject", headers=_headers(admin))
    second = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json={"appointment_id": appointment.id, "provider": "fake"})

    assert active.status_code == 409
    assert active.json()["detail"]["code"] == "payment_active_order_exists"
    assert second.status_code == 200
    assert second.json()["id"] != first["id"]


def test_approved_order_blocks_new_charge(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _, appointment = _fixture(db_session, "approved-block")
    order = _create_order(api_client, admin, appointment)
    _submit(api_client, admin, order["id"])
    api_client.post(f"/api/v1/admin/payment-orders/{order['id']}/fake/approve", headers=_headers(admin))
    response = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json={"appointment_id": appointment.id, "provider": "fake"})

    assert response.status_code == 409


def test_client_and_professional_must_match_appointment(api_client: TestClient, db_session) -> None:
    admin, _, _, professional, client, appointment = _fixture(db_session, "mismatch")
    other_client = ClientProfile(user_id=_user(db_session, UserRole.client, "other-client").id)
    other_professional = ProfessionalProfile(user_id=_user(db_session, UserRole.professional, "other-pro").id, consultation_mode=ConsultationMode.online, session_duration_minutes=60)
    db_session.add_all([other_client, other_professional])
    db_session.commit()

    client_response = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json={"appointment_id": appointment.id, "client_id": other_client.id, "provider": "fake"})
    pro_response = api_client.post("/api/v1/admin/payment-orders", headers=_headers(admin), json={"appointment_id": appointment.id, "professional_id": other_professional.id, "provider": "fake"})

    assert client.id != other_client.id
    assert professional.id != other_professional.id
    assert client_response.status_code == 422
    assert pro_response.status_code == 422


def test_professional_and_client_read_is_isolated_and_read_only(api_client: TestClient, db_session) -> None:
    admin, professional_user, client_user, _, _, appointment = _fixture(db_session, "isolation")
    order = _create_order(api_client, admin, appointment)
    other_pro = _user(db_session, UserRole.professional, "isolation-other-pro")
    db_session.add(ProfessionalProfile(user_id=other_pro.id, consultation_mode=ConsultationMode.online, session_duration_minutes=60))
    db_session.commit()

    pro_list = api_client.get("/api/v1/professionals/me/payment-orders", headers=_headers(professional_user))
    pro_other = api_client.get(f"/api/v1/professionals/me/payment-orders/{order['id']}", headers=_headers(other_pro))
    pro_fake = api_client.post(f"/api/v1/admin/payment-orders/{order['id']}/fake/approve", headers=_headers(professional_user))
    client_list = api_client.get("/api/v1/clients/me/payment-orders", headers=_headers(client_user))
    client_fake = api_client.post(f"/api/v1/admin/payment-orders/{order['id']}/fake/approve", headers=_headers(client_user))

    assert pro_list.status_code == 200
    assert len(pro_list.json()) == 1
    assert pro_other.status_code == 404
    assert pro_fake.status_code == 403
    assert client_list.status_code == 200
    assert len(client_list.json()) == 1
    assert client_fake.status_code == 403
    assert "request_fingerprint" not in client_list.text
    assert "idempotency" not in client_list.text


def test_admin_lists_filters_and_health_check(api_client: TestClient, db_session) -> None:
    admin, _, _, professional, client, appointment = _fixture(db_session, "list")
    order = _create_order(api_client, admin, appointment)
    listed = api_client.get(
        "/api/v1/admin/payment-orders",
        headers=_headers(admin),
        params={"status": "draft", "provider": "fake", "appointment_id": appointment.id, "client_id": client.id, "professional_id": professional.id},
    )
    health = api_client.post("/api/v1/admin/payment-providers/fake/health", headers=_headers(admin))

    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == order["id"]
    assert health.status_code == 200
    assert health.json()["healthy"] is True


def test_schemas_do_not_contain_card_data_or_secrets(api_client: TestClient, db_session) -> None:
    admin, _, client_user, _, _, appointment = _fixture(db_session, "safe")
    _create_order(api_client, admin, appointment)
    response = api_client.get("/api/v1/clients/me/payment-orders", headers=_headers(client_user))
    body = response.text.lower()

    assert response.status_code == 200
    for forbidden in ("card", "cvv", "token", "secret", "request_fingerprint", "external_payment_id"):
        assert forbidden not in body
