from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.availability import AvailabilityBlock, AvailabilityRule
from app.models.professional_profile import ProfessionalProfile
from app.models.user import UserRole
from app.schemas.availability import (
    AvailabilityBlockCreate,
    AvailabilityBlockRead,
    AvailabilityRuleCreate,
    AvailabilityRuleRead,
    AvailabilityRuleUpdate,
    AvailabilitySlot,
)
from app.services.availability import AvailabilityService

router = APIRouter()


@router.get("/professionals/{professional_id}/availability", response_model=list[AvailabilitySlot])
def list_availability(
    professional_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
) -> list[AvailabilitySlot]:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    slots = AvailabilityService(db).list_slots(professional, start, end)
    return [AvailabilitySlot(**slot) for slot in slots]


@router.post("/professionals/me/availability-rules", response_model=AvailabilityRuleRead, dependencies=[Depends(require_roles(UserRole.professional))])
def create_rule(payload: AvailabilityRuleCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AvailabilityRuleRead:
    professional = AvailabilityService(db).get_professional_by_user(user.id)
    rule = AvailabilityService(db).create_rule(professional, payload)
    return AvailabilityRuleRead.model_validate(rule)


@router.patch(
    "/professionals/me/availability-rules/{rule_id}",
    response_model=AvailabilityRuleRead,
    dependencies=[Depends(require_roles(UserRole.professional))],
)
def update_rule(rule_id: int, payload: AvailabilityRuleUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AvailabilityRuleRead:
    professional = AvailabilityService(db).get_professional_by_user(user.id)
    rule = db.get(AvailabilityRule, rule_id)
    if not rule or rule.professional_id != professional.id:
        raise HTTPException(status_code=404, detail="Rule not found")
    item = AvailabilityService(db).update_rule(rule, payload)
    return AvailabilityRuleRead.model_validate(item)


@router.delete("/professionals/me/availability-rules/{rule_id}", dependencies=[Depends(require_roles(UserRole.professional))])
def delete_rule(rule_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    professional = AvailabilityService(db).get_professional_by_user(user.id)
    rule = db.get(AvailabilityRule, rule_id)
    if not rule or rule.professional_id != professional.id:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}


@router.post("/professionals/me/availability-blocks", response_model=AvailabilityBlockRead, dependencies=[Depends(require_roles(UserRole.professional))])
def create_block(payload: AvailabilityBlockCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AvailabilityBlockRead:
    professional = AvailabilityService(db).get_professional_by_user(user.id)
    block = AvailabilityService(db).create_block(professional, payload)
    return AvailabilityBlockRead.model_validate(block)


@router.delete("/professionals/me/availability-blocks/{block_id}", dependencies=[Depends(require_roles(UserRole.professional))])
def delete_block(block_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    professional = AvailabilityService(db).get_professional_by_user(user.id)
    block = db.get(AvailabilityBlock, block_id)
    if not block or block.professional_id != professional.id:
        raise HTTPException(status_code=404, detail="Block not found")
    db.delete(block)
    db.commit()
    return {"message": "Block deleted"}
