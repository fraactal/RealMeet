from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class IntegrationResult:
    success: bool
    code: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    skipped: bool = False
    external_id: str | None = None
    execution_id: int | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def duration_ms(self) -> int:
        return max(int((self.finished_at - self.started_at).total_seconds() * 1000), 0)

    @classmethod
    def ok(cls, *, code: str, message: str, metadata: dict[str, Any] | None = None, external_id: str | None = None) -> "IntegrationResult":
        started_at = datetime.now(UTC)
        return cls(
            success=True,
            code=code,
            message=message,
            metadata=metadata or {},
            external_id=external_id,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )

    @classmethod
    def failed(cls, *, code: str, message: str, metadata: dict[str, Any] | None = None) -> "IntegrationResult":
        started_at = datetime.now(UTC)
        return cls(success=False, code=code, message=message, metadata=metadata or {}, started_at=started_at, finished_at=datetime.now(UTC))

    @classmethod
    def skipped_idempotent(cls, *, message: str, metadata: dict[str, Any] | None = None) -> "IntegrationResult":
        started_at = datetime.now(UTC)
        return cls(
            success=True,
            code="already_processed",
            message=message,
            metadata=metadata or {},
            skipped=True,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
