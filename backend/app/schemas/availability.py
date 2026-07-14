from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator

from app.models.availability import AvailabilityBlockType
from app.schemas.common import ORMModel


class AvailabilityRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_range(self) -> "AvailabilityRuleCreate":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AvailabilityRuleUpdate(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "AvailabilityRuleUpdate":
        if self.start_time is not None and self.end_time is not None and self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


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

    @model_validator(mode="after")
    def validate_datetime_range(self) -> "AvailabilityBlockCreate":
        if self.start_datetime >= self.end_datetime:
            raise ValueError("start_datetime must be before end_datetime")
        return self


class AvailabilityBlockUpdate(BaseModel):
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    reason: str | None = None
    type: AvailabilityBlockType | None = None

    @model_validator(mode="after")
    def validate_datetime_range(self) -> "AvailabilityBlockUpdate":
        if self.start_datetime is not None and self.end_datetime is not None and self.start_datetime >= self.end_datetime:
            raise ValueError("start_datetime must be before end_datetime")
        return self


class AvailabilityBlockRead(ORMModel):
    id: int
    professional_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: str | None
    type: AvailabilityBlockType


class AvailableSlotRead(BaseModel):
    start_datetime: datetime
    end_datetime: datetime


class AvailabilityResponse(BaseModel):
    professional_id: int
    start_datetime: datetime
    end_datetime: datetime
    slots: list[AvailableSlotRead]


AvailabilitySlot = AvailableSlotRead
