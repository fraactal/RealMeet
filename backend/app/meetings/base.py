from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class MeetingPayload:
    provider: str
    url: str
    external_id: str | None = None
    calendar_event_id: str | None = None
    status: str = "active"
    created_at: datetime | None = None


class MeetingProvider(ABC):
    @abstractmethod
    def create_meeting(self, professional_name: str, starts_at: datetime) -> MeetingPayload:
        raise NotImplementedError

    def cancel_meeting(self, external_id: str) -> MeetingPayload:
        return MeetingPayload(provider=self.provider_name, url="", external_id=external_id, status="inactive", created_at=datetime.now(UTC))

    def get_meeting(self, external_id: str) -> MeetingPayload:
        return MeetingPayload(provider=self.provider_name, url="", external_id=external_id, status="unknown", created_at=datetime.now(UTC))

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__.replace("Provider", "").lower()
