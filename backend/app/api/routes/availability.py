from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_professional
from app.db.session import get_db
from app.models.professional_profile import ProfessionalProfile
from app.schemas.availability import (
    AvailabilityBlockCreate,
    AvailabilityBlockRead,
    AvailabilityBlockUpdate,
    AvailabilityResponse,
    AvailabilityRuleCreate,
    AvailabilityRuleRead,
    AvailabilityRuleUpdate,
)
from app.services.availability import AvailabilityService

router = APIRouter()


@router.get("/professionals/{professional_id}/availability", response_model=AvailabilityResponse)
def list_availability(
    professional_id: int,
    target_date: date | None = Query(default=None, alias="date"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    start_datetime, end_datetime = _resolve_availability_range(target_date, date_from, date_to, start, end)
    slots = AvailabilityService(db).list_slots(professional, start_datetime, end_datetime)
    return AvailabilityResponse(
        professional_id=professional.id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        slots=slots,
    )


@router.get("/professionals/me/availability-rules", response_model=list[AvailabilityRuleRead], dependencies=[Depends(require_professional)])
def list_rules(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[AvailabilityRuleRead]:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    return [AvailabilityRuleRead.model_validate(rule) for rule in service.list_rules(professional)]


@router.post("/professionals/me/availability-rules", response_model=AvailabilityRuleRead, dependencies=[Depends(require_professional)])
def create_rule(payload: AvailabilityRuleCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AvailabilityRuleRead:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    rule = service.create_rule(professional, payload)
    return AvailabilityRuleRead.model_validate(rule)


@router.patch(
    "/professionals/me/availability-rules/{rule_id}",
    response_model=AvailabilityRuleRead,
    dependencies=[Depends(require_professional)],
)
def update_rule(rule_id: int, payload: AvailabilityRuleUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AvailabilityRuleRead:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    rule = service.get_rule_for_professional(professional, rule_id)
    item = service.update_rule(rule, payload)
    return AvailabilityRuleRead.model_validate(item)


@router.delete("/professionals/me/availability-rules/{rule_id}", dependencies=[Depends(require_professional)])
def delete_rule(rule_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    rule = service.get_rule_for_professional(professional, rule_id)
    service.delete_rule(rule)
    return {"message": "Rule deleted"}


@router.get("/professionals/me/availability-blocks", response_model=list[AvailabilityBlockRead], dependencies=[Depends(require_professional)])
def list_blocks(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[AvailabilityBlockRead]:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    return [AvailabilityBlockRead.model_validate(block) for block in service.list_blocks(professional)]


@router.post("/professionals/me/availability-blocks", response_model=AvailabilityBlockRead, dependencies=[Depends(require_professional)])
def create_block(payload: AvailabilityBlockCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AvailabilityBlockRead:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    block = service.create_block(professional, payload)
    return AvailabilityBlockRead.model_validate(block)


@router.patch(
    "/professionals/me/availability-blocks/{block_id}",
    response_model=AvailabilityBlockRead,
    dependencies=[Depends(require_professional)],
)
def update_block(
    block_id: int,
    payload: AvailabilityBlockUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvailabilityBlockRead:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    block = service.get_block_for_professional(professional, block_id)
    item = service.update_block(block, payload)
    return AvailabilityBlockRead.model_validate(item)


@router.delete("/professionals/me/availability-blocks/{block_id}", dependencies=[Depends(require_professional)])
def delete_block(block_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    service = AvailabilityService(db)
    professional = service.get_professional_by_user(user.id)
    block = service.get_block_for_professional(professional, block_id)
    service.delete_block(block)
    return {"message": "Block deleted"}


def _resolve_availability_range(
    target_date: date | None,
    date_from: date | None,
    date_to: date | None,
    start: datetime | None,
    end: datetime | None,
) -> tuple[datetime, datetime]:
    if target_date:
        return _day_range(target_date)
    if date_from or date_to:
        if not date_from or not date_to:
            raise HTTPException(status_code=400, detail="date_from and date_to are required together")
        start_datetime = datetime.combine(date_from, time.min, tzinfo=UTC)
        end_datetime = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
        return start_datetime, end_datetime
    if start and end:
        return start, end
    raise HTTPException(status_code=400, detail="Provide date, date_from/date_to, or start/end")


def _day_range(value: date) -> tuple[datetime, datetime]:
    start_datetime = datetime.combine(value, time.min, tzinfo=UTC)
    end_datetime = start_datetime + timedelta(days=1)
    return start_datetime, end_datetime
