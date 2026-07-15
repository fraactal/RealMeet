from __future__ import annotations

import hmac
import hashlib
import re
from dataclasses import dataclass

from app.core.config import settings
from app.whatsapp.exceptions import WhatsAppValidationError


COUNTRY_CALLING_CODES = {
    "CL": "56",
    "US": "1",
    "CA": "1",
    "MX": "52",
    "AR": "54",
    "BR": "55",
    "CO": "57",
    "PE": "51",
    "UY": "598",
    "ES": "34",
}


@dataclass(frozen=True)
class NormalizedPhone:
    e164: str
    masked: str


def normalize_phone(value: str, *, default_country_code: str | None = None) -> NormalizedPhone:
    raw = (value or "").strip()
    if not raw:
        raise WhatsAppValidationError("El telefono es obligatorio", code="phone_required")
    if re.search(r"[A-Za-z]", raw):
        raise WhatsAppValidationError("El telefono no puede contener letras", code="phone_invalid")
    if re.search(r"(ext\.?|x)\s*\d+", raw, flags=re.IGNORECASE):
        raise WhatsAppValidationError("El telefono no puede incluir extension", code="phone_extension_not_allowed")
    if re.search(r"[^0-9+()\-\s.]", raw):
        raise WhatsAppValidationError("El telefono contiene caracteres no permitidos", code="phone_invalid")
    if raw.count("+") > 1 or ("+" in raw and not raw.startswith("+")):
        raise WhatsAppValidationError("El signo + solo puede ir al inicio", code="phone_invalid")

    digits = re.sub(r"\D", "", raw)
    if len(digits) < 8 or len(digits) > 15:
        raise WhatsAppValidationError("El telefono debe tener entre 8 y 15 digitos", code="phone_invalid_length")

    if raw.startswith("+"):
        e164_digits = digits
    else:
        country = (default_country_code or settings.whatsapp_default_country_code or "").strip().upper()
        if not country:
            raise WhatsAppValidationError("El telefono requiere pais explicito", code="phone_country_required")
        calling_code = COUNTRY_CALLING_CODES.get(country)
        if not calling_code:
            raise WhatsAppValidationError("El pais no esta soportado para normalizacion local", code="phone_country_unsupported")
        e164_digits = f"{calling_code}{digits.lstrip('0')}"

    if len(e164_digits) < 8 or len(e164_digits) > 15:
        raise WhatsAppValidationError("El telefono normalizado no cumple E.164", code="phone_invalid_length")
    return NormalizedPhone(e164=f"+{e164_digits}", masked=mask_phone_e164(f"+{e164_digits}"))


def mask_phone_e164(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 8:
        raise WhatsAppValidationError("El telefono no se puede enmascarar", code="phone_invalid")
    country = _country_code_from_digits(digits)
    subscriber = digits[len(country) :]
    visible_prefix = subscriber[:1]
    visible_suffix = subscriber[-4:]
    return f"+{country} {visible_prefix} **** {visible_suffix}"


def phone_hmac(e164_phone: str, *, key: str | None = None) -> str:
    secret = (key if key is not None else settings.whatsapp_phone_hmac_key) or ""
    if not secret.strip():
        raise WhatsAppValidationError("WHATSAPP_PHONE_HMAC_KEY es requerida para correlacion privada", code="phone_hmac_key_missing")
    return hmac.new(secret.strip().encode("utf-8"), e164_phone.encode("utf-8"), hashlib.sha256).hexdigest()


def _country_code_from_digits(digits: str) -> str:
    for length in (3, 2, 1):
        candidate = digits[:length]
        if candidate in set(COUNTRY_CALLING_CODES.values()):
            return candidate
    return digits[:2]
