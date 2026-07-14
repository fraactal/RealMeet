from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.auth import ClientRegisterRequest, LoginRequest, TokenResponse
from app.schemas.users import ClientProfileCreate, UserCreate, UserRead
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user = AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post("/register-client", response_model=UserRead)
def register_client(payload: ClientRegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    user = AuthService(db).register(payload.user, payload.client_profile)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = AuthService(db).login(payload.email, payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
def me(user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
