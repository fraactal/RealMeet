from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_client
from app.db.session import get_db
from app.schemas.users import ClientSelfProfileRead, ClientSelfProfileUpdate, UserRead, UserSelfUpdate
from app.services.profiles import ProfileService
from app.whatsapp.enums import WhatsAppConsentPurpose
from app.whatsapp.exceptions import WhatsAppError, WhatsAppNotFoundError
from app.whatsapp.schemas import WhatsAppConsentGrant, WhatsAppConsentRead
from app.whatsapp.services import WhatsAppConsentService

router = APIRouter()


@router.get("/me", response_model=UserRead)
def get_me(user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
def patch_me(payload: UserSelfUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> UserRead:
    db_user = ProfileService(db).update_user_self(user, payload)
    return UserRead.model_validate(db_user)


@router.get("/me/profile", response_model=ClientSelfProfileRead, dependencies=[Depends(require_client)])
def get_my_client_profile(user=Depends(get_current_user), db: Session = Depends(get_db)) -> ClientSelfProfileRead:
    return ProfileService(db).get_client_self_profile(user)


@router.patch("/me/profile", response_model=ClientSelfProfileRead, dependencies=[Depends(require_client)])
def update_my_client_profile(
    payload: ClientSelfProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientSelfProfileRead:
    return ProfileService(db).update_client_self_profile(user, payload)


@router.get("/me/whatsapp-consents", response_model=list[WhatsAppConsentRead])
def list_my_whatsapp_consents(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[WhatsAppConsentRead]:
    return [WhatsAppConsentRead.model_validate(item) for item in WhatsAppConsentService(db).list_for_user(user)]


@router.post("/me/whatsapp-consents", response_model=WhatsAppConsentRead)
def grant_my_whatsapp_consent(
    payload: WhatsAppConsentGrant,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WhatsAppConsentRead:
    try:
        consent = WhatsAppConsentService(db).grant_self_service(user, payload)
    except WhatsAppError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return WhatsAppConsentRead.model_validate(consent)


@router.delete("/me/whatsapp-consents/{purpose}", response_model=WhatsAppConsentRead)
def revoke_my_whatsapp_consent(
    purpose: WhatsAppConsentPurpose,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WhatsAppConsentRead:
    try:
        consent = WhatsAppConsentService(db).revoke_self_service(user, purpose)
    except WhatsAppNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except WhatsAppError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return WhatsAppConsentRead.model_validate(consent)
