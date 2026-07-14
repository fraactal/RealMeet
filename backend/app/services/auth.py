from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.client_profile import ClientProfile
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.users import ClientProfileCreate, UserCreate


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: UserCreate, client_profile: ClientProfileCreate | None = None) -> User:
        if self.users.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            role=payload.role,
        )
        self.db.add(user)
        self.db.flush()

        if payload.role == UserRole.client:
            self.db.add(
                ClientProfile(
                    user_id=user.id,
                    birth_date=client_profile.birth_date if client_profile else None,
                    notes=client_profile.notes if client_profile else None,
                )
            )

        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email.lower())
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return create_access_token(str(user.id))
