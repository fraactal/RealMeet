from app.payments.enums import PaymentOrderStatus


ACTIVE_PAYMENT_STATUSES = {
    PaymentOrderStatus.draft,
    PaymentOrderStatus.pending,
    PaymentOrderStatus.requires_action,
}
FINAL_PAYMENT_STATUSES = {
    PaymentOrderStatus.approved,
    PaymentOrderStatus.rejected,
    PaymentOrderStatus.cancelled,
    PaymentOrderStatus.expired,
    PaymentOrderStatus.failed,
    PaymentOrderStatus.refunded,
}

VALID_PAYMENT_TRANSITIONS: dict[PaymentOrderStatus, set[PaymentOrderStatus]] = {
    PaymentOrderStatus.draft: {PaymentOrderStatus.pending},
    PaymentOrderStatus.pending: {
        PaymentOrderStatus.requires_action,
        PaymentOrderStatus.approved,
        PaymentOrderStatus.rejected,
        PaymentOrderStatus.cancelled,
        PaymentOrderStatus.expired,
        PaymentOrderStatus.failed,
        PaymentOrderStatus.refunded,
    },
    PaymentOrderStatus.requires_action: {
        PaymentOrderStatus.approved,
        PaymentOrderStatus.rejected,
        PaymentOrderStatus.cancelled,
        PaymentOrderStatus.expired,
        PaymentOrderStatus.failed,
    },
}


def can_transition(previous: PaymentOrderStatus, new: PaymentOrderStatus) -> bool:
    return new in VALID_PAYMENT_TRANSITIONS.get(previous, set())
