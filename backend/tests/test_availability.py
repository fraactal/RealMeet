from datetime import UTC, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.availability import AvailabilityBlockType
from app.schemas.availability import AvailabilityBlockCreate, AvailabilityRuleCreate
from app.services.availability import AvailabilityService


class FakeSession:
    def __init__(self, scalar_result=None, scalars_results=None) -> None:
        self.scalar_result = scalar_result
        self.scalars_results = iter(scalars_results or [])

    def scalar(self, *_):
        return self.scalar_result

    def scalars(self, *_):
        return next(self.scalars_results)

    def add(self, *_):
        return None

    def commit(self):
        return None

    def refresh(self, *_):
        return None


def test_availability_rule_rejects_invalid_time_range() -> None:
    with pytest.raises(ValidationError):
        AvailabilityRuleCreate(weekday=1, start_time=time(10, 0), end_time=time(10, 0))


def test_availability_block_rejects_invalid_datetime_range() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        AvailabilityBlockCreate(start_datetime=now, end_datetime=now - timedelta(hours=1))


def test_availability_rule_overlap_is_rejected() -> None:
    existing_rule = SimpleNamespace(id=1)
    service = AvailabilityService(FakeSession(scalar_result=existing_rule))

    with pytest.raises(HTTPException) as exc_info:
        service.create_rule(
            SimpleNamespace(id=1),
            AvailabilityRuleCreate(weekday=1, start_time=time(9, 0), end_time=time(12, 0)),
        )

    assert exc_info.value.status_code == 409


def test_availability_slots_exclude_blocked_interval() -> None:
    target_day = datetime.now(UTC).date() + timedelta(days=7)
    start = datetime.combine(target_day, time(9, 0), tzinfo=UTC)
    end = datetime.combine(target_day, time(12, 0), tzinfo=UTC)
    rule = SimpleNamespace(weekday=target_day.weekday(), start_time=time(9, 0), end_time=time(12, 0))
    block = SimpleNamespace(
        start_datetime=datetime.combine(target_day, time(10, 0), tzinfo=UTC),
        end_datetime=datetime.combine(target_day, time(11, 0), tzinfo=UTC),
        type=AvailabilityBlockType.blocked,
    )
    service = AvailabilityService(FakeSession(scalars_results=[[rule], [block], []]))

    slots = service.list_slots(SimpleNamespace(id=1, session_duration_minutes=60), start, end, include_external=False)

    assert slots == [
        {"start_datetime": datetime.combine(target_day, time(9, 0), tzinfo=UTC), "end_datetime": datetime.combine(target_day, time(10, 0), tzinfo=UTC)},
        {"start_datetime": datetime.combine(target_day, time(11, 0), tzinfo=UTC), "end_datetime": datetime.combine(target_day, time(12, 0), tzinfo=UTC)},
    ]
