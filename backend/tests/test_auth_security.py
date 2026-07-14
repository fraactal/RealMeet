from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.deps import get_current_user, require_admin, require_client, require_professional
from app.core.security import ALGORITHM, create_access_token, decode_token, hash_password
from app.models.user import UserRole
from app.schemas.users import ClientSelfProfileUpdate, UserSelfUpdate
from app.services.auth import AuthService


def test_decode_token_accepts_valid_token() -> None:
    token = create_access_token("1")

    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert "exp" in payload


def test_decode_token_rejects_invalid_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not-a-valid-token")

    assert exc_info.value.status_code == 401


def test_decode_token_rejects_expired_token() -> None:
    token = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_non_numeric_subject() -> None:
    token = jwt.encode(
        {"sub": "abc", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=SimpleNamespace(get=lambda *_: None), token=token)

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_inactive_user() -> None:
    token = create_access_token("1")
    inactive_user = SimpleNamespace(id=1, role=UserRole.client, is_active=False)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=SimpleNamespace(get=lambda *_: inactive_user), token=token)

    assert exc_info.value.status_code == 401


def test_login_rejects_inactive_user() -> None:
    service = AuthService.__new__(AuthService)
    service.users = SimpleNamespace(
        get_by_email=lambda *_: SimpleNamespace(id=1, is_active=False, password_hash=hash_password("Client123!"))
    )

    with pytest.raises(HTTPException) as exc_info:
        service.login("client@realmeet.local", "Client123!")

    assert exc_info.value.status_code == 401


def test_role_helpers_allow_matching_roles() -> None:
    admin = SimpleNamespace(role=UserRole.admin)
    professional = SimpleNamespace(role=UserRole.professional)
    client = SimpleNamespace(role=UserRole.client)

    assert require_admin(admin) is admin
    assert require_professional(professional) is professional
    assert require_client(client) is client


def test_role_helpers_reject_wrong_role() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_admin(SimpleNamespace(role=UserRole.client))

    assert exc_info.value.status_code == 403


def test_user_self_update_contract_excludes_admin_fields() -> None:
    payload = UserSelfUpdate.model_validate({"first_name": "Client", "is_active": False, "role": "admin"})

    data = payload.model_dump(exclude_unset=True)

    assert data == {"first_name": "Client"}


def test_client_self_profile_update_contract_excludes_admin_fields() -> None:
    payload = ClientSelfProfileUpdate.model_validate(
        {"first_name": "Client", "birth_date": "1990-01-01", "is_active": False, "user_id": 99}
    )

    data = payload.model_dump(exclude_unset=True)

    assert set(data) == {"first_name", "birth_date"}
