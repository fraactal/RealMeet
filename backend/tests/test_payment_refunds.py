from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
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
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.main import app
from app.models.appointment import Appointment, AppointmentHistory, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import Integration, IntegrationExecution
from app.models.payment import PaymentOrder, PaymentOrderStatusHistory, PaymentRefund, PaymentRefundReasonCode, PaymentRefundStatus, PaymentRefundStatusHistory
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.payments.enums import PaymentCurrency, PaymentOrderStatus, PaymentProviderKey
from app.payments.providers.mercado_pago import MercadoPagoRefundResult

RUN_ID = uuid4().hex[:8]


class FakeMercadoPagoRefundClient:
    create_calls = 0
    get_calls = 0
    idempotency_keys: list[str] = []
    status = "approved"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def create_refund(self, payment_id: str, *, amount: Decimal, currency: PaymentCurrency, idempotency_key: str) -> MercadoPagoRefundResult:
        type(self).create_calls += 1
        type(self).idempotency_keys.append(idempotency_key)
        return MercadoPagoRefundResult(
            external_refund_id=f"mp-ref-{type(self).create_calls}",
            status=type(self).status,
            amount=amount,
            currency=currency,
            processed_at=datetime.now(UTC) if type(self).status == "approved" else None,
            provider_reference={"provider": "mercado_pago", "operation": "create_refund"},
        )

    def get_refund(self, payment_id: str, refund_id: str, *, currency: PaymentCurrency = PaymentCurrency.CLP) -> MercadoPagoRefundResult:
        type(self).get_calls += 1
        return MercadoPagoRefundResult(
            external_refund_id=refund_id,
            status=type(self).status,
            amount=Decimal("10000"),
            currency=currency,
            processed_at=datetime.now(UTC) if type(self).status == "approved" else None,
            provider_reference={"provider": "mercado_pago", "operation": "get_refund"},
        )


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        user_ids = list(db.scalars(select(User.id).where(User.email.like(f"test-17-4-{RUN_ID}-%@realmeet.local"))))
        if user_ids:
            professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.user_id.in_(user_ids))))
            client_ids = list(db.scalars(select(ClientProfile.id).where(ClientProfile.user_id.in_(user_ids))))
            appointment_ids = list(db.scalars(select(Appointment.id).where(Appointment.professional_id.in_(professional_ids)))) if professional_ids else []
            order_ids = list(db.scalars(select(PaymentOrder.id).where(PaymentOrder.appointment_id.in_(appointment_ids)))) if appointment_ids else []
            if order_ids:
                refund_ids = list(db.scalars(select(PaymentRefund.id).where(PaymentRefund.payment_order_id.in_(order_ids))))
                if refund_ids:
                    db.execute(delete(PaymentRefundStatusHistory).where(PaymentRefundStatusHistory.refund_id.in_(refund_ids)))
                    db.execute(delete(PaymentRefund).where(PaymentRefund.id.in_(refund_ids)))
                db.execute(delete(PaymentOrderStatusHistory).where(PaymentOrderStatusHistory.payment_order_id.in_(order_ids)))
                db.execute(delete(PaymentOrder).where(PaymentOrder.id.in_(order_ids)))
            if appointment_ids:
                db.execute(delete(AppointmentHistory).where(AppointmentHistory.appointment_id.in_(appointment_ids)))
                db.execute(delete(Appointment).where(Appointment.id.in_(appointment_ids)))
            if professional_ids:
                db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.id.in_(professional_ids)))
            if client_ids:
                db.execute(delete(ClientProfile).where(ClientProfile.id.in_(client_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name.in_(["PaymentRefund", "PaymentOrder"])))
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        integrations = list(db.scalars(select(Integration.id).where(Integration.name.like(f"Test 17.4 {RUN_ID}%"))))
        if integrations:
            db.execute(delete(IntegrationExecution).where(IntegrationExecution.integration_id.in_(integrations)))
            db.execute(delete(Integration).where(Integration.id.in_(integrations)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client(monkeypatch) -> TestClient:
    settings.rate_limit_enabled = False
    monkeypatch.setenv("MERCADO_PAGO_ACCESS_TOKEN_TEST", "TEST-token-redacted")
    monkeypatch.setenv("MERCADO_PAGO_WEBHOOK_SECRET_TEST", "webhook-secret")
    FakeMercadoPagoRefundClient.create_calls = 0
    FakeMercadoPagoRefundClient.get_calls = 0
    FakeMercadoPagoRefundClient.idempotency_keys = []
    FakeMercadoPagoRefundClient.status = "approved"
    monkeypatch.setattr("app.payments.refunds.mercado_pago_client_factory", lambda token: FakeMercadoPagoRefundClient(token))
    return TestClient(app)


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-17-4-{RUN_ID}-{suffix}-{role.value}@realmeet.local",
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


def _fixture(db, *, provider: PaymentProviderKey = PaymentProviderKey.fake, amount: Decimal = Decimal("35000"), suffix: str = "base"):
    admin = _user(db, UserRole.admin, f"{suffix}-admin")
    professional_user = _user(db, UserRole.professional, f"{suffix}-pro")
    client_user = _user(db, UserRole.client, f"{suffix}-client")
    professional = ProfessionalProfile(user_id=professional_user.id, title=f"Test 17.4 {suffix}", consultation_mode=ConsultationMode.online, session_duration_minutes=60, price=amount, is_public=True)
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    appointment = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        start_datetime=datetime.now(UTC) + timedelta(days=4),
        end_datetime=datetime.now(UTC) + timedelta(days=4, hours=1),
        status=AppointmentStatus.confirmed,
        consultation_mode=ConsultationMode.online,
        client_notes=f"Test 17.4 {suffix}",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    order = PaymentOrder(
        appointment_id=appointment.id,
        client_id=client.id,
        professional_id=professional.id,
        provider=provider,
        external_payment_id=f"{provider.value}-pay-{suffix}",
        status=PaymentOrderStatus.approved,
        amount=amount,
        currency=PaymentCurrency.CLP,
        description="Pago aprobado test 17.4",
        paid_at=datetime.now(UTC),
        idempotency_key=f"order-{RUN_ID}-{suffix}",
        request_fingerprint=f"fp-{RUN_ID}-{suffix}",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return admin, professional_user, client_user, appointment, order


def _create_refund(api_client: TestClient, admin: User, order_id: int, amount: str = "10000", key: str | None = None, summary: str | None = "Solicitud administrativa") -> dict:
    headers = _headers(admin)
    if key:
        headers["Idempotency-Key"] = key
    response = api_client.post(
        f"/api/v1/admin/payment-orders/{order_id}/refunds",
        headers=headers,
        json={"amount": amount, "currency": "CLP", "reason_code": "appointment_cancelled", "reason_summary": summary},
    )
    assert response.status_code == 200, response.text
    return response.json()



def _sign(data_id: str, request_id: str, secret: str = "webhook-secret") -> str:
    ts = "1704908010"
    digest = hmac.new(secret.encode(), f"id:{data_id.lower()};request-id:{request_id};ts:{ts};".encode(), hashlib.sha256).hexdigest()
    return f"ts={ts},v1={digest}"
def _mp_integration(db) -> None:
    db.add(
        Integration(
            name=f"Test 17.4 {RUN_ID} MP",
            integration_type=IntegrationType.payment,
            provider=IntegrationProvider.mercado_pago,
            enabled=True,
            status=IntegrationStatus.healthy,
            config={
                "environment": "sandbox",
                "country": "CL",
                "currency": "CLP",
                "notification_url": "http://localhost:18000/api/v1/webhooks/mercado-pago",
                "success_url": "http://localhost:15173/payments/success",
                "pending_url": "http://localhost:15173/payments/pending",
                "failure_url": "http://localhost:15173/payments/failure",
                "auto_return": "approved",
                "access_token_reference": "MERCADO_PAGO_ACCESS_TOKEN_TEST",
                "webhook_secret_reference": "MERCADO_PAGO_WEBHOOK_SECRET_TEST",
            },
        )
    )
    db.commit()


def test_fake_refund_total_partial_summary_and_appointment_is_unchanged(api_client: TestClient, db_session) -> None:
    admin, _, _, appointment, order = _fixture(db_session, suffix="fake-flow")
    partial = _create_refund(api_client, admin, order.id, "10000")
    submitted = api_client.post(f"/api/v1/admin/payment-refunds/{partial['id']}/submit", headers=_headers(admin))
    order_after_partial = api_client.get(f"/api/v1/admin/payment-orders/{order.id}", headers=_headers(admin))
    total = _create_refund(api_client, admin, order.id, "25000", key="test-17-4-total")
    api_client.post(f"/api/v1/admin/payment-refunds/{total['id']}/submit", headers=_headers(admin))
    order_after_total = api_client.get(f"/api/v1/admin/payment-orders/{order.id}", headers=_headers(admin))
    db_session.refresh(appointment)

    assert submitted.status_code == 200
    assert submitted.json()["status"] == "approved"
    assert order_after_partial.json()["refund_status"] == "partially_refunded"
    assert order_after_partial.json()["status"] == "approved"
    assert order_after_total.json()["refund_status"] == "refunded"
    assert order_after_total.json()["status"] == "refunded"
    assert appointment.status == AppointmentStatus.confirmed


def test_refund_validations_idempotency_and_sensitive_data_are_enforced(api_client: TestClient, db_session) -> None:
    admin, _, _, _, order = _fixture(db_session, suffix="validation")
    invalid_zero = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers=_headers(admin), json={"amount": "0", "currency": "CLP", "reason_code": "client_request"})
    invalid_fraction = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers=_headers(admin), json={"amount": "1.5", "currency": "CLP", "reason_code": "client_request"})
    invalid_sensitive = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers=_headers(admin), json={"amount": "1000", "currency": "CLP", "reason_code": "other", "reason_summary": "token secreto"})
    first = _create_refund(api_client, admin, order.id, "10000", key="refund-idem")
    second = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers={**_headers(admin), "Idempotency-Key": "refund-idem"}, json={"amount": "10000", "currency": "CLP", "reason_code": "appointment_cancelled", "reason_summary": "Solicitud administrativa"})
    conflict = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers={**_headers(admin), "Idempotency-Key": "refund-idem"}, json={"amount": "11000", "currency": "CLP", "reason_code": "appointment_cancelled", "reason_summary": "Solicitud administrativa"})
    too_much = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers=_headers(admin), json={"amount": "36000", "currency": "CLP", "reason_code": "client_request"})

    assert invalid_zero.status_code == 422
    assert invalid_fraction.status_code == 422
    assert invalid_sensitive.status_code == 422
    assert second.status_code == 200
    assert second.json()["id"] == first["id"]
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "payment_refund_idempotency_conflict"
    assert too_much.status_code == 422
    assert "secret" not in str(first).lower()


def test_fake_reject_fail_reconcile_and_events_are_sanitized(api_client: TestClient, db_session) -> None:
    admin, _, _, _, order = _fixture(db_session, suffix="fake-controls")
    rejected = _create_refund(api_client, admin, order.id, "5000", summary="reject")
    failed = _create_refund(api_client, admin, order.id, "5000", key="refund-fail", summary="fail")
    reject_response = api_client.post(f"/api/v1/admin/payment-refunds/{rejected['id']}/submit", headers=_headers(admin))
    fail_response = api_client.post(f"/api/v1/admin/payment-refunds/{failed['id']}/submit", headers=_headers(admin))
    reconcile = api_client.post(f"/api/v1/admin/payment-refunds/{failed['id']}/reconcile", headers=_headers(admin))
    events = db_session.scalars(select(AuditLog).where(AuditLog.entity_name == "PaymentRefund")).all()

    assert reject_response.json()["status"] == "rejected"
    assert fail_response.json()["status"] == "failed"
    assert reconcile.status_code == 200
    assert any(event.metadata_json["event_type"] == "payment.refund.requested" for event in events)
    assert any(event.metadata_json["event_type"] == "payment.refund.rejected" for event in events)
    assert any(event.metadata_json["event_type"] == "payment.refund.failed" for event in events)
    assert "idempotency" not in str([event.metadata_json for event in events]).lower()
    assert "token" not in fail_response.text.lower()


def test_mercado_pago_refund_submit_sync_retry_and_no_real_network(api_client: TestClient, db_session, monkeypatch) -> None:
    _mp_integration(db_session)
    admin, _, _, _, order = _fixture(db_session, provider=PaymentProviderKey.mercado_pago, suffix="mp")
    refund = _create_refund(api_client, admin, order.id, "10000", key="mp-refund")
    submit = api_client.post(f"/api/v1/admin/payment-refunds/{refund['id']}/submit", headers=_headers(admin))
    retry = api_client.post(f"/api/v1/admin/payment-refunds/{refund['id']}/retry", headers=_headers(admin))
    FakeMercadoPagoRefundClient.status = "mystery"
    sync = api_client.post(f"/api/v1/admin/payment-refunds/{refund['id']}/sync-provider", headers=_headers(admin))

    assert submit.status_code == 200
    assert submit.json()["status"] == "approved"
    assert retry.json()["external_refund_id"] == submit.json()["external_refund_id"]
    assert FakeMercadoPagoRefundClient.create_calls == 1
    assert FakeMercadoPagoRefundClient.idempotency_keys[0].endswith(":provider:create-refund")
    assert sync.json()["status"] in {"approved", "reconcile_required"}


def test_refund_permissions_are_admin_write_and_owner_read_only(api_client: TestClient, db_session) -> None:
    admin, professional_user, client_user, _, order = _fixture(db_session, suffix="permissions")
    refund = _create_refund(api_client, admin, order.id, "10000")
    pro_list = api_client.get(f"/api/v1/professionals/me/payment-orders/{order.id}/refunds", headers=_headers(professional_user))
    client_list = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/refunds", headers=_headers(client_user))
    pro_create = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/refunds", headers=_headers(professional_user), json={"amount": "1000", "currency": "CLP", "reason_code": "client_request"})
    client_fake = api_client.post(f"/api/v1/admin/payment-refunds/{refund['id']}/fake/approve", headers=_headers(client_user))
    other_client = _user(db_session, UserRole.client, "other")
    db_session.add(ClientProfile(user_id=other_client.id))
    db_session.commit()
    other_read = api_client.get(f"/api/v1/clients/me/payment-orders/{order.id}/refunds", headers=_headers(other_client))

    assert pro_list.status_code == 200
    assert client_list.status_code == 200
    assert pro_list.json()[0]["id"] == refund["id"]
    assert client_list.json()[0]["id"] == refund["id"]
    assert pro_create.status_code == 403
    assert client_fake.status_code == 403
    assert other_read.status_code == 404


def test_order_reconcile_corrects_refund_summary_and_detects_amount_inconsistency(api_client: TestClient, db_session) -> None:
    admin, _, _, _, order = _fixture(db_session, suffix="reconcile")
    refund = PaymentRefund(payment_order_id=order.id, provider=PaymentProviderKey.fake, amount=Decimal("10000"), currency=PaymentCurrency.CLP, reason_code=PaymentRefundReasonCode.client_request, status=PaymentRefundStatus.approved, requested_by_user_id=admin.id, requested_at=datetime.now(UTC), processed_at=datetime.now(UTC))
    db_session.add(refund)
    order.refunded_amount = Decimal("0")
    order.refund_status = "not_refunded"
    db_session.commit()
    fixed = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/reconcile", headers=_headers(admin))
    refund2 = PaymentRefund(payment_order_id=order.id, provider=PaymentProviderKey.fake, amount=Decimal("40000"), currency=PaymentCurrency.CLP, reason_code=PaymentRefundReasonCode.client_request, status=PaymentRefundStatus.approved, requested_by_user_id=admin.id, requested_at=datetime.now(UTC), processed_at=datetime.now(UTC))
    db_session.add(refund2)
    db_session.commit()
    inconsistent = api_client.post(f"/api/v1/admin/payment-orders/{order.id}/reconcile", headers=_headers(admin))

    assert fixed.status_code == 200
    assert fixed.json()["result"] == "refund_sync_required"
    assert fixed.json()["payment_order"]["refund_status"] == "partially_refunded"
    assert inconsistent.json()["result"] == "refund_amount_inconsistent"


def test_refund_webhook_is_recorded_for_manual_sync(api_client: TestClient, db_session) -> None:
    admin, _, _, _, _ = _fixture(db_session, suffix="webhook")
    _mp_integration(db_session)
    del admin
    request_id = f"refund-request-{RUN_ID}"
    headers = {"x-request-id": request_id, "x-signature": _sign("123", request_id)}
    response = api_client.post("/api/v1/webhooks/mercado-pago", headers=headers, json={"id": f"refund-{RUN_ID}", "type": "refund.updated", "data": {"id": "123"}})
    duplicate = api_client.post("/api/v1/webhooks/mercado-pago", headers=headers, json={"id": f"refund-{RUN_ID}", "type": "refund.updated", "data": {"id": "123"}})

    assert response.status_code == 200
    assert response.json()["result"] in {"refund_sync_required", "invalid_signature"}
    assert duplicate.json()["result"] == "duplicate"

def test_admin_payment_responses_do_not_expose_idempotency_or_fingerprints(api_client: TestClient, db_session) -> None:
    admin, _, _, _, order = _fixture(db_session, suffix="no-sensitive-response")
    refund = _create_refund(api_client, admin, order.id, "10000", key="hidden-refund-key")
    order_response = api_client.get(f"/api/v1/admin/payment-orders/{order.id}", headers=_headers(admin))
    refund_response = api_client.get(f"/api/v1/admin/payment-refunds/{refund['id']}", headers=_headers(admin))

    assert order_response.status_code == 200
    assert refund_response.status_code == 200
    for forbidden in ("idempotency_key", "request_fingerprint", "hidden-refund-key", f"fp-{RUN_ID}"):
        assert forbidden not in order_response.text
        assert forbidden not in refund_response.text