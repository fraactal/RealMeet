from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_client
from app.db.session import get_db
from app.schemas.users import ClientSelfProfileRead, ClientSelfProfileUpdate, UserRead, UserSelfUpdate
from app.services.profiles import ProfileService

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
