from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import authentication_exception, decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    try:
        user_pk = int(user_id)
    except (TypeError, ValueError) as exc:
        raise authentication_exception() from exc
    if user_pk <= 0:
        raise authentication_exception()
    user = db.get(User, user_pk)
    if not user or not user.is_active:
        raise authentication_exception()
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency
