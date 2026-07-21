from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class MemoryMetadata:
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_access: datetime | None = None
    usage_frequency: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "last_access": self.last_access.isoformat() if self.last_access is not None else None,
            "usage_frequency": self.usage_frequency,
        }


class MetadataFactory:
    @staticmethod
    def create() -> MemoryMetadata:
        now = datetime.now()
        return MemoryMetadata(
            created_at=now,
            updated_at=now,
            access_count=0,
            last_access=None,
            usage_frequency=0.0,
        )

    @staticmethod
    def update(meta: MemoryMetadata) -> MemoryMetadata:
        now = datetime.now()
        elapsed = (now - meta.updated_at).total_seconds()
        if elapsed > 0:
            alpha = 0.1
            instant_freq = 1.0 / elapsed if elapsed > 0 else 0.0
            freq = (1 - alpha) * meta.usage_frequency + alpha * instant_freq
        else:
            freq = meta.usage_frequency
        return MemoryMetadata(
            created_at=meta.created_at,
            updated_at=now,
            access_count=meta.access_count + 1,
            last_access=now,
            usage_frequency=freq,
        )
