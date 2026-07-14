from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.deps import get_current_user, require_admin, require_client, require_professional
from app.core.security import ALGORITHM, create_access_token, decode_token, hash_password
from app.models.user import UserRole
from app.schemas.categories import CategoryAdminRead, CategoryPublicRead
from app.schemas.professionals import (
    ProfessionalPublicCategoryRead,
    ProfessionalPublicProfileUpdate,
    ProfessionalPublicRead,
    ProfessionalPublicUserRead,
    ProfessionalSelfProfileUpdate,
    ProfessionalSpecialtyRead,
    ProfessionalSpecialtyUpdate,
)
from app.schemas.specialties import SpecialtyAdminRead, SpecialtyPublicRead
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


def test_professional_self_profile_update_contract_excludes_future_and_admin_fields() -> None:
    payload = ProfessionalSelfProfileUpdate.model_validate(
        {
            "first_name": "Professional",
            "title": "Psicologa",
            "category_id": 1,
            "specialty_ids": [1],
            "price": "45000",
            "is_public": False,
            "is_verified": True,
            "professional_license": "ABC",
            "is_active": False,
            "role": "admin",
        }
    )

    data = payload.model_dump(exclude_unset=True)

    assert data == {"first_name": "Professional", "title": "Psicologa"}


def test_public_catalog_contracts_exclude_admin_state() -> None:
    category = CategoryPublicRead(id=1, name="Salud", slug="salud", description=None)
    specialty = SpecialtyPublicRead(id=1, category_id=1, name="Psicologia", slug="psicologia", description=None)

    assert "is_active" not in category.model_dump()
    assert "is_active" not in specialty.model_dump()


def test_admin_catalog_contracts_include_admin_state() -> None:
    category = CategoryAdminRead(id=1, name="Salud", slug="salud", description=None, is_active=True)
    specialty = SpecialtyAdminRead(
        id=1,
        category_id=1,
        name="Psicologia",
        slug="psicologia",
        description=None,
        is_active=True,
    )

    assert category.is_active is True
    assert specialty.is_active is True


def test_professional_specialty_update_keeps_requested_ids() -> None:
    payload = ProfessionalSpecialtyUpdate.model_validate({"specialty_ids": [1, 2, 2]})

    assert payload.specialty_ids == [1, 2, 2]


def test_professional_public_contract_excludes_sensitive_fields() -> None:
    payload = ProfessionalPublicRead(
        id=1,
        title="Psicologa clinica",
        bio="Atencion adultos",
        years_experience=8,
        consultation_mode="online",
        session_duration_minutes=50,
        city="Santiago",
        country="Chile",
        user=ProfessionalPublicUserRead(id=2, first_name="Ana", last_name="Lopez"),
        category=ProfessionalPublicCategoryRead(id=1, name="Salud", slug="salud"),
        specialties=[
            ProfessionalSpecialtyRead(
                id=1,
                name="Psicologia",
                slug="psicologia",
                category_id=1,
                category_name="Salud",
            )
        ],
    )

    data = payload.model_dump()

    assert "email" not in data["user"]
    assert "phone" not in data["user"]
    assert "is_active" not in data["user"]
    assert "price" not in data
    assert "address" not in data
    assert "professional_license" not in data
    assert "is_verified" not in data


def test_professional_public_profile_update_excludes_admin_fields() -> None:
    payload = ProfessionalPublicProfileUpdate.model_validate(
        {
            "category_id": 1,
            "is_public": True,
            "title": "Psicologa",
            "professional_license": "ABC",
            "is_verified": True,
            "price": "45000",
            "address": "Private",
            "user_id": 99,
        }
    )

    data = payload.model_dump(exclude_unset=True)

    assert data == {"category_id": 1, "is_public": True, "title": "Psicologa"}
