from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User, UserRole
from app.schemas.appointments import AppointmentAdminRead
from app.schemas.professionals import ProfessionalProfileRead
from app.schemas.users import UserRead, UserUpdate

router = APIRouter(dependencies=[Depends(require_roles(UserRole.admin))])


@router.get("/users", response_model=list[UserRead])
def list_users(limit: int = Query(default=20, le=100), offset: int = Query(default=0), db: Session = Depends(get_db)) -> list[UserRead]:
    items = list(db.scalars(select(User).offset(offset).limit(limit).order_by(User.created_at.desc())))
    return [UserRead.model_validate(item) for item in items]


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)


@router.get("/professionals", response_model=list[ProfessionalProfileRead])
def list_professionals(limit: int = Query(default=20, le=100), offset: int = Query(default=0), db: Session = Depends(get_db)) -> list[ProfessionalProfileRead]:
    items = list(db.scalars(select(ProfessionalProfile).offset(offset).limit(limit).order_by(ProfessionalProfile.created_at.desc())))
    return [ProfessionalProfileRead.model_validate(item) for item in items]


@router.patch("/professionals/{professional_id}", response_model=ProfessionalProfileRead)
def patch_professional(professional_id: int, payload: dict, db: Session = Depends(get_db)) -> ProfessionalProfileRead:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    for key, value in payload.items():
        if hasattr(professional, key):
            setattr(professional, key, value)
    db.commit()
    db.refresh(professional)
    return ProfessionalProfileRead.model_validate(professional)


@router.get("/appointments", response_model=list[AppointmentAdminRead])
def list_appointments(limit: int = Query(default=20, le=100), offset: int = Query(default=0), db: Session = Depends(get_db)) -> list[AppointmentAdminRead]:
    items = list(db.scalars(select(Appointment).offset(offset).limit(limit).order_by(Appointment.start_datetime.desc())))
    return [AppointmentAdminRead.model_validate(item) for item in items]
