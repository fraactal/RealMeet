from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin, require_client, require_professional
from app.db.session import get_db
from app.models.user import User
from app.payments.enums import PaymentOrderStatus, PaymentProviderKey
from app.payments.schemas import (
    PaymentOrderAdminRead,
    PaymentOrderCancel,
    PaymentOrderCreate,
    PaymentOrderListResponse,
    PaymentOrderPublicRead,
    PaymentOrderStatusHistoryRead,
    PaymentCheckoutAction,
    PaymentCheckoutRead,
    PaymentProviderHealthRead,
    PaymentReconcileRead,
)
from app.payments.service import PaymentOrderService
from app.schemas.admin import PageMeta

router = APIRouter()


def _page_meta(page: int, page_size: int, total: int) -> PageMeta:
    total_pages = max((total + page_size - 1) // page_size, 1)
    return PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


@router.get("/admin/payment-orders", response_model=PaymentOrderListResponse, dependencies=[Depends(require_admin)])
def list_admin_payment_orders(
    status_filter: PaymentOrderStatus | None = Query(default=None, alias="status"),
    provider: PaymentProviderKey | None = Query(default=None),
    appointment_id: int | None = Query(default=None),
    client_id: int | None = Query(default=None),
    professional_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaymentOrderListResponse:
    items, total = PaymentOrderService(db).list_admin(
        status_filter=status_filter,
        provider=provider,
        appointment_id=appointment_id,
        client_id=client_id,
        professional_id=professional_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaymentOrderListResponse(items=[PaymentOrderAdminRead.model_validate(item) for item in items], meta=_page_meta(page, page_size, total))


@router.post("/admin/payment-orders", response_model=PaymentOrderAdminRead)
def create_admin_payment_order(
    payload: PaymentOrderCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(PaymentOrderService(db).create(payload, admin_user, idempotency_key))


@router.get("/admin/payment-orders/{payment_order_id}", response_model=PaymentOrderAdminRead, dependencies=[Depends(require_admin)])
def get_admin_payment_order(payment_order_id: int, db: Session = Depends(get_db)) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(PaymentOrderService(db).get(payment_order_id))


@router.post("/admin/payment-orders/{payment_order_id}/submit", response_model=PaymentOrderAdminRead)
async def submit_admin_payment_order(
    payment_order_id: int,
    payload: dict | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PaymentOrderAdminRead:
    body_key = payload.get("idempotency_key") if isinstance(payload, dict) else None
    return PaymentOrderAdminRead.model_validate(await PaymentOrderService(db).submit(payment_order_id, admin_user, idempotency_key or body_key))


@router.post("/admin/payment-orders/{payment_order_id}/cancel", response_model=PaymentOrderAdminRead)
async def cancel_admin_payment_order(
    payment_order_id: int,
    payload: PaymentOrderCancel | None = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(await PaymentOrderService(db).cancel(payment_order_id, admin_user, payload))


@router.get("/admin/payment-orders/{payment_order_id}/history", response_model=list[PaymentOrderStatusHistoryRead], dependencies=[Depends(require_admin)])
def list_admin_payment_order_history(payment_order_id: int, db: Session = Depends(get_db)) -> list[PaymentOrderStatusHistoryRead]:
    PaymentOrderService(db).get(payment_order_id)
    return [PaymentOrderStatusHistoryRead.model_validate(item) for item in PaymentOrderService(db).list_history(payment_order_id)]


@router.post("/admin/payment-orders/{payment_order_id}/fake/approve", response_model=PaymentOrderAdminRead)
def approve_fake_payment_order(payment_order_id: int, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(PaymentOrderService(db).fake_approve(payment_order_id, admin_user))


@router.post("/admin/payment-orders/{payment_order_id}/fake/reject", response_model=PaymentOrderAdminRead)
def reject_fake_payment_order(payment_order_id: int, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(PaymentOrderService(db).fake_reject(payment_order_id, admin_user))


@router.post("/admin/payment-orders/{payment_order_id}/fake/expire", response_model=PaymentOrderAdminRead)
def expire_fake_payment_order(payment_order_id: int, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(PaymentOrderService(db).fake_expire(payment_order_id, admin_user))


@router.post("/admin/payment-orders/{payment_order_id}/fake/fail", response_model=PaymentOrderAdminRead)
def fail_fake_payment_order(payment_order_id: int, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> PaymentOrderAdminRead:
    return PaymentOrderAdminRead.model_validate(PaymentOrderService(db).fake_fail(payment_order_id, admin_user))


@router.post("/admin/payment-orders/{payment_order_id}/reconcile", response_model=PaymentReconcileRead)
def reconcile_admin_payment_order(payment_order_id: int, admin_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> PaymentReconcileRead:
    result, item = PaymentOrderService(db).reconcile(payment_order_id, admin_user)
    return PaymentReconcileRead(result=result, payment_order=PaymentOrderAdminRead.model_validate(item))


@router.post("/admin/payment-providers/{provider}/health", response_model=PaymentProviderHealthRead)
async def health_payment_provider(
    provider: PaymentProviderKey,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PaymentProviderHealthRead:
    del admin_user
    result = await PaymentOrderService(db).health(provider)
    return PaymentProviderHealthRead(provider=provider, healthy=result.healthy, code=result.code, message=result.message)


@router.get("/professionals/me/payment-orders", response_model=list[PaymentOrderPublicRead], dependencies=[Depends(require_professional)])
def list_professional_payment_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PaymentOrderPublicRead]:
    return [PaymentOrderPublicRead.model_validate(item) for item in PaymentOrderService(db).list_for_professional(user)]


@router.get("/professionals/me/payment-orders/{payment_order_id}", response_model=PaymentOrderPublicRead, dependencies=[Depends(require_professional)])
def get_professional_payment_order(payment_order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOrderPublicRead:
    return PaymentOrderPublicRead.model_validate(PaymentOrderService(db).get_for_professional(payment_order_id, user))


@router.get("/clients/me/payment-orders", response_model=list[PaymentOrderPublicRead], dependencies=[Depends(require_client)])
def list_client_payment_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PaymentOrderPublicRead]:
    return [PaymentOrderPublicRead.model_validate(item) for item in PaymentOrderService(db).list_for_client(user)]


@router.get("/clients/me/payment-orders/{payment_order_id}", response_model=PaymentOrderPublicRead, dependencies=[Depends(require_client)])
def get_client_payment_order(payment_order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOrderPublicRead:
    return PaymentOrderPublicRead.model_validate(PaymentOrderService(db).get_for_client(payment_order_id, user))


@router.get("/clients/me/payment-orders/{payment_order_id}/checkout", response_model=PaymentCheckoutRead, dependencies=[Depends(require_client)])
def get_client_payment_checkout(payment_order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentCheckoutRead:
    return PaymentOrderService(db).checkout_for_client(payment_order_id, user)


@router.post("/clients/me/payment-orders/{payment_order_id}/checkout/approve", response_model=PaymentOrderPublicRead, dependencies=[Depends(require_client)])
def approve_client_payment_checkout(payment_order_id: int, payload: PaymentCheckoutAction | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOrderPublicRead:
    del payload
    return PaymentOrderPublicRead.model_validate(PaymentOrderService(db).approve_checkout_for_client(payment_order_id, user))


@router.post("/clients/me/payment-orders/{payment_order_id}/checkout/reject", response_model=PaymentOrderPublicRead, dependencies=[Depends(require_client)])
def reject_client_payment_checkout(payment_order_id: int, payload: PaymentCheckoutAction | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOrderPublicRead:
    del payload
    return PaymentOrderPublicRead.model_validate(PaymentOrderService(db).reject_checkout_for_client(payment_order_id, user))
