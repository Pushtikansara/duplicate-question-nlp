from __future__ import annotations

from dataclasses import dataclass

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


@dataclass
class RoutingContext:
    question_a: str
    question_b: str
    cross_encoder_score: float | None = None
    perception_metadata: PerceptionMetadata | None = None
    semantic_assessment: SemanticAssessment | None = None
    reasoning_result: ReasoningResult | None = None
