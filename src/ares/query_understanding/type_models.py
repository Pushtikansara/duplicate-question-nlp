from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class QuestionTypeResult:
    question_1_type: str = "other"
    question_2_type: str = "other"
    pair_type: str = "unknown"
    classification_confidence: float = 0.0
    classification_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_1_type": self.question_1_type,
            "question_2_type": self.question_2_type,
            "pair_type": self.pair_type,
            "classification_confidence": self.classification_confidence,
            "classification_reason": self.classification_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuestionTypeResult:
        return cls(
            question_1_type=data.get("question_1_type", "other"),
            question_2_type=data.get("question_2_type", "other"),
            pair_type=data.get("pair_type", "unknown"),
            classification_confidence=data.get("classification_confidence", 0.0),
            classification_reason=data.get("classification_reason", ""),
        )
