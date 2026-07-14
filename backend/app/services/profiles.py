from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client_profile import ClientProfile
from app.models.user import User
from app.schemas.users import ClientSelfProfileRead, ClientSelfProfileUpdate, UserRead, UserSelfUpdate


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_user_self(self, user: User, payload: UserSelfUpdate) -> User:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_client_self_profile(self, user: User) -> ClientSelfProfileRead:
        profile = self._get_or_create_client_profile(user)
        return self._serialize_client_profile(user, profile)

    def update_client_self_profile(self, user: User, payload: ClientSelfProfileUpdate) -> ClientSelfProfileRead:
        profile = self._get_or_create_client_profile(user)
        data = payload.model_dump(exclude_unset=True)
        for key in ("first_name", "last_name", "phone"):
            if key in data:
                setattr(user, key, data[key])
        for key in ("birth_date", "notes"):
            if key in data:
                setattr(profile, key, data[key])
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(profile)
        return self._serialize_client_profile(user, profile)

    def _get_or_create_client_profile(self, user: User) -> ClientProfile:
        profile = self.db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
        if profile:
            return profile
        profile = ClientProfile(user_id=user.id)
        self.db.add(profile)
        self.db.flush()
        return profile

    @staticmethod
    def _serialize_client_profile(user: User, profile: ClientProfile) -> ClientSelfProfileRead:
        return ClientSelfProfileRead(
            user=UserRead.model_validate(user),
            birth_date=profile.birth_date,
            notes=profile.notes,
        )
