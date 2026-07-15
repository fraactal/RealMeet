from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.whatsapp.exceptions import WhatsAppError, WhatsAppValidationError
from app.whatsapp.schemas import WhatsAppWebhookReceiveRead
from app.whatsapp.services import WhatsAppWebhookService

router = APIRouter()


@router.get("/whatsapp/webhook")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    db: Session = Depends(get_db),
):
    try:
        result = WhatsAppWebhookService(db).verify_callback(mode=hub_mode, verify_token=hub_verify_token, challenge=hub_challenge)
    except WhatsAppValidationError as exc:
        return _webhook_error(exc)
    return PlainTextResponse(result.challenge or "", status_code=status.HTTP_200_OK)


@router.post("/whatsapp/webhook", response_model=WhatsAppWebhookReceiveRead)
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
) -> WhatsAppWebhookReceiveRead | JSONResponse:
    raw_body = await request.body()
    try:
        result = WhatsAppWebhookService(db).receive(raw_body=raw_body, signature_header=x_hub_signature_256)
    except WhatsAppValidationError as exc:
        return _webhook_error(exc)
    return WhatsAppWebhookReceiveRead(**result.__dict__)


def _webhook_error(exc: WhatsAppError) -> JSONResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    if exc.code == "webhook_body_too_large":
        status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    elif exc.code in {"webhook_verify_token_invalid", "webhook_signature_invalid"}:
        status_code = status.HTTP_403_FORBIDDEN
    elif exc.code == "webhook_signature_missing":
        status_code = status.HTTP_401_UNAUTHORIZED
    elif exc.code in {"webhook_verify_token_missing", "webhook_app_secret_missing"}:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content={"detail": exc.message, "code": exc.code})
