from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryConfig:
    max_entries: int = 10000
    max_versions: int = 10
    default_ttl_days: int = 365
    enable_consolidation: bool = True
    enable_audit: bool = True
    enable_forgetting: bool = True
    auto_consolidate_interval: int = 1000
    aging_threshold_days: int = 90
    quality_threshold: float = 0.3
    confidence_threshold: float = 0.2
    store_type: str = "in_memory"


class MemoryConfigLoader:
    @staticmethod
    def load_default() -> MemoryConfig:
        return MemoryConfig()

    @staticmethod
    def from_dict(data: dict[str, Any]) -> MemoryConfig:
        return MemoryConfig(
            max_entries=data.get("max_entries", 10000),
            max_versions=data.get("max_versions", 10),
            default_ttl_days=data.get("default_ttl_days", 365),
            enable_consolidation=data.get("enable_consolidation", True),
            enable_audit=data.get("enable_audit", True),
            enable_forgetting=data.get("enable_forgetting", True),
            auto_consolidate_interval=data.get("auto_consolidate_interval", 1000),
            aging_threshold_days=data.get("aging_threshold_days", 90),
            quality_threshold=data.get("quality_threshold", 0.3),
            confidence_threshold=data.get("confidence_threshold", 0.2),
            store_type=data.get("store_type", "in_memory"),
        )
