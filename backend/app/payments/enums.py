import enum


class PaymentCurrency(str, enum.Enum):
    CLP = "CLP"


class PaymentProviderKey(str, enum.Enum):
    fake = "fake"
    mercado_pago = "mercado_pago"
    stripe = "stripe"


class PaymentOrderStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    requires_action = "requires_action"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"
    expired = "expired"
    failed = "failed"
    refunded = "refunded"
