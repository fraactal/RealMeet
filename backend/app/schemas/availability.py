from datetime import datetime, time

from pydantic import BaseModel

from app.models.availability import AvailabilityBlockType
from app.schemas.common import ORMModel


class AvailabilityRuleCreate(BaseModel):
    weekday: int
    start_time: time
    end_time: time
    is_active: bool = True


class AvailabilityRuleUpdate(BaseModel):
    weekday: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None


class AvailabilityRuleRead(ORMModel):
    id: int
    professional_id: int
    weekday: int
    start_time: time
    end_time: time
    is_active: bool


class AvailabilityBlockCreate(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: str | None = None
    type: AvailabilityBlockType = AvailabilityBlockType.blocked


class AvailabilityBlockRead(ORMModel):
    id: int
    professional_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: str | None
    type: AvailabilityBlockType


class AvailabilitySlot(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
