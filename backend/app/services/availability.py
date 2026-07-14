from datetime import UTC, date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import AvailabilityBlock, AvailabilityBlockType, AvailabilityRule
from app.models.professional_profile import ProfessionalProfile
from app.schemas.availability import AvailabilityBlockCreate, AvailabilityBlockUpdate, AvailabilityRuleCreate, AvailabilityRuleUpdate


MAX_AVAILABILITY_RANGE_DAYS = 14
DEFAULT_SESSION_DURATION_MINUTES = 60
MIN_SESSION_DURATION_MINUTES = 5
MAX_SESSION_DURATION_MINUTES = 480


class AvailabilityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_rules(self, professional: ProfessionalProfile) -> list[AvailabilityRule]:
        return list(
            self.db.scalars(
                select(AvailabilityRule)
                .where(AvailabilityRule.professional_id == professional.id)
                .order_by(AvailabilityRule.weekday.asc(), AvailabilityRule.start_time.asc(), AvailabilityRule.id.asc())
            )
        )

    def create_rule(self, professional: ProfessionalProfile, payload: AvailabilityRuleCreate) -> AvailabilityRule:
        self._ensure_rule_is_valid(
            professional_id=professional.id,
            weekday=payload.weekday,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_active=payload.is_active,
        )
        rule = AvailabilityRule(professional_id=professional.id, **payload.model_dump())
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, rule: AvailabilityRule, payload: AvailabilityRuleUpdate) -> AvailabilityRule:
        data = payload.model_dump(exclude_unset=True)
        weekday = data.get("weekday", rule.weekday)
        start_time = data.get("start_time", rule.start_time)
        end_time = data.get("end_time", rule.end_time)
        is_active = data.get("is_active", rule.is_active)
        self._ensure_rule_is_valid(
            professional_id=rule.professional_id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
            exclude_rule_id=rule.id,
        )
        for key, value in data.items():
            setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule: AvailabilityRule) -> None:
        self.db.delete(rule)
        self.db.commit()

    def list_blocks(self, professional: ProfessionalProfile) -> list[AvailabilityBlock]:
        return list(
            self.db.scalars(
                select(AvailabilityBlock)
                .where(AvailabilityBlock.professional_id == professional.id)
                .order_by(AvailabilityBlock.start_datetime.asc(), AvailabilityBlock.id.asc())
            )
        )

    def create_block(self, professional: ProfessionalProfile, payload: AvailabilityBlockCreate) -> AvailabilityBlock:
        self._ensure_datetime_range(payload.start_datetime, payload.end_datetime)
        block = AvailabilityBlock(professional_id=professional.id, **payload.model_dump())
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def update_block(self, block: AvailabilityBlock, payload: AvailabilityBlockUpdate) -> AvailabilityBlock:
        data = payload.model_dump(exclude_unset=True)
        start_datetime = data.get("start_datetime", block.start_datetime)
        end_datetime = data.get("end_datetime", block.end_datetime)
        self._ensure_datetime_range(start_datetime, end_datetime)
        for key, value in data.items():
            setattr(block, key, value)
        self.db.commit()
        self.db.refresh(block)
        return block

    def delete_block(self, block: AvailabilityBlock) -> None:
        self.db.delete(block)
        self.db.commit()

    def get_rule_for_professional(self, professional: ProfessionalProfile, rule_id: int) -> AvailabilityRule:
        rule = self.db.get(AvailabilityRule, rule_id)
        if not rule or rule.professional_id != professional.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        return rule

    def get_block_for_professional(self, professional: ProfessionalProfile, block_id: int) -> AvailabilityBlock:
        block = self.db.get(AvailabilityBlock, block_id)
        if not block or block.professional_id != professional.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
        return block

    def list_slots(self, professional: ProfessionalProfile, start: datetime, end: datetime) -> list[dict]:
        start = self._ensure_aware_utc(start)
        end = self._ensure_aware_utc(end)
        self._ensure_query_range(start, end)
        duration_minutes = self._get_duration_minutes(professional)
        rules = list(
            self.db.scalars(
                select(AvailabilityRule)
                .where(AvailabilityRule.professional_id == professional.id, AvailabilityRule.is_active.is_(True))
                .order_by(AvailabilityRule.weekday.asc(), AvailabilityRule.start_time.asc())
            )
        )
        blocks = list(
            self.db.scalars(
                select(AvailabilityBlock).where(
                    AvailabilityBlock.professional_id == professional.id,
                    AvailabilityBlock.start_datetime < end,
                    AvailabilityBlock.end_datetime > start,
                    AvailabilityBlock.type == AvailabilityBlockType.blocked,
                )
            )
        )
        appointments = list(
            self.db.scalars(
                select(Appointment).where(
                    Appointment.professional_id == professional.id,
                    Appointment.start_datetime < end,
                    Appointment.end_datetime > start,
                    Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]),
                )
            )
        )
        slots: list[dict] = []
        now = datetime.now(UTC)
        for day in self._iter_dates(start.date(), end.date()):
            for rule in [rule for rule in rules if rule.weekday == day.weekday()]:
                interval_start = self._combine(day, rule.start_time)
                interval_end = self._combine(day, rule.end_time)
                slot_start = max(interval_start, start)
                slot_end_limit = min(interval_end, end)
                slot_start = self._align_to_rule_boundary(slot_start, interval_start, duration_minutes)
                while slot_start + timedelta(minutes=duration_minutes) <= slot_end_limit:
                    generated_end = slot_start + timedelta(minutes=duration_minutes)
                    blocked = any(self._ranges_overlap(block.start_datetime, block.end_datetime, slot_start, generated_end) for block in blocks)
                    occupied = any(
                        self._ranges_overlap(appointment.start_datetime, appointment.end_datetime, slot_start, generated_end)
                        for appointment in appointments
                    )
                    if slot_start >= now and not blocked and not occupied:
                        slots.append({"start_datetime": slot_start, "end_datetime": generated_end})
                    slot_start = generated_end
        return sorted(slots, key=lambda slot: slot["start_datetime"])

    def get_professional_by_user(self, user_id: int) -> ProfessionalProfile:
        profile = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id))
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional profile not found")
        return profile

    def _ensure_rule_is_valid(
        self,
        professional_id: int,
        weekday: int,
        start_time: time,
        end_time: time,
        is_active: bool,
        exclude_rule_id: int | None = None,
    ) -> None:
        if start_time >= end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rule start_time must be before end_time")
        if not is_active:
            return
        query = select(AvailabilityRule).where(
            AvailabilityRule.professional_id == professional_id,
            AvailabilityRule.weekday == weekday,
            AvailabilityRule.is_active.is_(True),
            AvailabilityRule.start_time < end_time,
            AvailabilityRule.end_time > start_time,
        )
        if exclude_rule_id is not None:
            query = query.where(AvailabilityRule.id != exclude_rule_id)
        if self.db.scalar(query):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Availability rule overlaps an existing rule")

    @staticmethod
    def _ensure_datetime_range(start_datetime: datetime, end_datetime: datetime) -> None:
        if start_datetime >= end_datetime:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Block start_datetime must be before end_datetime")

    @staticmethod
    def _ensure_query_range(start: datetime, end: datetime) -> None:
        if start >= end:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start must be before end")
        if end - start > timedelta(days=MAX_AVAILABILITY_RANGE_DAYS):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Availability range is too large")

    @staticmethod
    def _get_duration_minutes(professional: ProfessionalProfile) -> int:
        duration = professional.session_duration_minutes or DEFAULT_SESSION_DURATION_MINUTES
        if duration < MIN_SESSION_DURATION_MINUTES or duration > MAX_SESSION_DURATION_MINUTES:
            return DEFAULT_SESSION_DURATION_MINUTES
        return duration

    @staticmethod
    def _ensure_aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _combine(day: date, value: time) -> datetime:
        return datetime.combine(day, value, tzinfo=UTC)

    @staticmethod
    def _iter_dates(start_date: date, end_date: date):
        cursor = start_date
        while cursor <= end_date:
            yield cursor
            cursor = cursor + timedelta(days=1)

    @staticmethod
    def _ranges_overlap(first_start: datetime, first_end: datetime, second_start: datetime, second_end: datetime) -> bool:
        return first_start < second_end and first_end > second_start

    @staticmethod
    def _align_to_rule_boundary(slot_start: datetime, interval_start: datetime, duration_minutes: int) -> datetime:
        if slot_start <= interval_start:
            return interval_start
        minutes_from_start = int((slot_start - interval_start).total_seconds() // 60)
        remainder = minutes_from_start % duration_minutes
        if remainder == 0:
            return slot_start.replace(second=0, microsecond=0)
        return (slot_start + timedelta(minutes=duration_minutes - remainder)).replace(second=0, microsecond=0)
