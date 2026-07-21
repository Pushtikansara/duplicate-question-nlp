from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TrustLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationType(Enum):
    ACCEPT = "accept"
    LOW_CONFIDENCE_WARNING = "low_confidence_warning"
    HUMAN_REVIEW = "human_review"
    RE_RUN_FULL = "re_run_full"
    RE_RUN_DIFFERENT_ROUTING = "re_run_different_routing"
    MEMORY_REFRESH_SUGGESTED = "memory_refresh_suggested"


@dataclass
class AuditorResult:
    module: str
    score: float
    details: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    passed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "score": self.score,
            "details": self.details,
            "warnings": self.warnings,
            "passed": self.passed,
        }


@dataclass
class ConsistencyWarning:
    warning_type: str
    description: str
    severity: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "warning_type": self.warning_type,
            "description": self.description,
            "severity": self.severity,
            "details": self.details,
        }


class RoutingAuditorABC(ABC):
    @abstractmethod
    def audit(self, routing_result: Any) -> AuditorResult: ...


class ReasoningAuditorABC(ABC):
    @abstractmethod
    def audit(self, reasoning_result: Any) -> AuditorResult: ...


class DebateAuditorABC(ABC):
    @abstractmethod
    def audit(self, debate_result: Any) -> AuditorResult: ...


class MemoryAuditorABC(ABC):
    @abstractmethod
    def audit(self, memory_manager: Any, context: Any) -> AuditorResult: ...


class ConfidenceAuditorABC(ABC):
    @abstractmethod
    def audit(self, prediction: dict[str, Any], calibration_data: dict[str, Any] | None) -> AuditorResult: ...


class ReflectionPlugin(ABC):
    @abstractmethod
    def before_reflection(self, context: Any) -> Any: ...

    @abstractmethod
    def after_reflection(self, result: Any) -> Any: ...

    @abstractmethod
    def name(self) -> str: ...
