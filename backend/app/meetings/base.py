from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MeetingPayload:
    provider: str
    url: str
    external_id: str | None = None
    calendar_event_id: str | None = None


class MeetingProvider(ABC):
    @abstractmethod
    def create_meeting(self, professional_name: str, starts_at: datetime) -> MeetingPayload:
        raise NotImplementedError
