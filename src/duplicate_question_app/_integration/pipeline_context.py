from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineContext:
    question_a: str
    question_b: str
    perception_result: Any = None
    routing_result: Any = None
    retrieved_memories: list[Any] = field(default_factory=list)
    semantic_assessment: Any = None
    reasoning_result: Any = None
    debate_result: Any = None
    prediction_result: dict[str, Any] = field(default_factory=dict)
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            elif key == "retrieved_memories":
                result[key] = [m.to_dict() if hasattr(m, "to_dict") else str(m) for m in value]
            else:
                result[key] = value
        return result
