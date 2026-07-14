from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.availability import AvailabilityBlock, AvailabilityRule
from app.models.professional_profile import ProfessionalProfile
from app.schemas.availability import AvailabilityBlockCreate, AvailabilityRuleCreate, AvailabilityRuleUpdate


class AvailabilityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_rule(self, professional: ProfessionalProfile, payload: AvailabilityRuleCreate) -> AvailabilityRule:
        rule = AvailabilityRule(professional_id=professional.id, **payload.model_dump())
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, rule: AvailabilityRule, payload: AvailabilityRuleUpdate) -> AvailabilityRule:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def create_block(self, professional: ProfessionalProfile, payload: AvailabilityBlockCreate) -> AvailabilityBlock:
        block = AvailabilityBlock(professional_id=professional.id, **payload.model_dump())
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def list_slots(self, professional: ProfessionalProfile, start: datetime, end: datetime) -> list[dict]:
        rules = list(
            self.db.scalars(
                select(AvailabilityRule).where(AvailabilityRule.professional_id == professional.id, AvailabilityRule.is_active.is_(True))
            )
        )
        blocks = list(
            self.db.scalars(
                select(AvailabilityBlock).where(
                    AvailabilityBlock.professional_id == professional.id,
                    AvailabilityBlock.start_datetime < end,
                    AvailabilityBlock.end_datetime > start,
                )
            )
        )
        appointments = list(
            self.db.scalars(
                select(Appointment).where(
                    Appointment.professional_id == professional.id,
                    Appointment.start_datetime < end,
                    Appointment.end_datetime > start,
                )
            )
        )
        slots: list[dict] = []
        cursor = start
        while cursor < end:
            for rule in [r for r in rules if r.weekday == cursor.weekday()]:
                slot_start = cursor.replace(hour=rule.start_time.hour, minute=rule.start_time.minute, second=0, microsecond=0)
                slot_end = cursor.replace(hour=rule.end_time.hour, minute=rule.end_time.minute, second=0, microsecond=0)
                while slot_start + timedelta(minutes=professional.session_duration_minutes) <= slot_end:
                    generated_end = slot_start + timedelta(minutes=professional.session_duration_minutes)
                    blocked = any(b.start_datetime < generated_end and b.end_datetime > slot_start for b in blocks)
                    occupied = any(a.start_datetime < generated_end and a.end_datetime > slot_start for a in appointments)
                    if not blocked and not occupied:
                        slots.append({"start_datetime": slot_start, "end_datetime": generated_end})
                    slot_start = generated_end
            cursor = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return slots

    def get_professional_by_user(self, user_id: int) -> ProfessionalProfile:
        profile = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id))
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional profile not found")
        return profile
