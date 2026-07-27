from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DIFFICULTY_VERY_EASY = "Very Easy"
DIFFICULTY_EASY = "Easy"
DIFFICULTY_MEDIUM = "Medium"
DIFFICULTY_HARD = "Hard"
DIFFICULTY_VERY_HARD = "Very Hard"

DIFFICULTY_LEVELS = [
    DIFFICULTY_VERY_EASY,
    DIFFICULTY_EASY,
    DIFFICULTY_MEDIUM,
    DIFFICULTY_HARD,
    DIFFICULTY_VERY_HARD,
]


def score_to_difficulty(score: float) -> str:
    if score < 0.1:
        return DIFFICULTY_VERY_EASY
    if score < 0.25:
        return DIFFICULTY_EASY
    if score < 0.45:
        return DIFFICULTY_MEDIUM
    if score < 0.65:
        return DIFFICULTY_HARD
    return DIFFICULTY_VERY_HARD


@dataclass
class ComplexityAnalysis:
    overall_complexity_score: float = 0.0
    difficulty_level: str = DIFFICULTY_VERY_EASY

    lexical_complexity: float = 0.0
    syntactic_complexity: float = 0.0
    semantic_complexity: float = 0.0
    entity_complexity: float = 0.0
    ambiguity_score: float = 0.0
    readability_score: float = 0.0
    comparison_difficulty: float = 0.0

    rare_token_density: float = 0.0
    entity_density: float = 0.0
    numeric_density: float = 0.0
    abbreviation_density: float = 0.0
    sentence_complexity: float = 0.0
    question_length_score: float = 0.0
    token_diversity: float = 0.0

    confidence_estimate: float = 1.0
    risk_score: float = 0.0

    reasoning_summary: str = ""
    processing_time: float = 0.0
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_complexity_score": self.overall_complexity_score,
            "difficulty_level": self.difficulty_level,
            "lexical_complexity": self.lexical_complexity,
            "syntactic_complexity": self.syntactic_complexity,
            "semantic_complexity": self.semantic_complexity,
            "entity_complexity": self.entity_complexity,
            "ambiguity_score": self.ambiguity_score,
            "readability_score": self.readability_score,
            "comparison_difficulty": self.comparison_difficulty,
            "rare_token_density": self.rare_token_density,
            "entity_density": self.entity_density,
            "numeric_density": self.numeric_density,
            "abbreviation_density": self.abbreviation_density,
            "sentence_complexity": self.sentence_complexity,
            "question_length_score": self.question_length_score,
            "token_diversity": self.token_diversity,
            "confidence_estimate": self.confidence_estimate,
            "risk_score": self.risk_score,
            "reasoning_summary": self.reasoning_summary,
            "processing_time": self.processing_time,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplexityAnalysis:
        return cls(
            overall_complexity_score=data.get("overall_complexity_score", 0.0),
            difficulty_level=data.get("difficulty_level", DIFFICULTY_VERY_EASY),
            lexical_complexity=data.get("lexical_complexity", 0.0),
            syntactic_complexity=data.get("syntactic_complexity", 0.0),
            semantic_complexity=data.get("semantic_complexity", 0.0),
            entity_complexity=data.get("entity_complexity", 0.0),
            ambiguity_score=data.get("ambiguity_score", 0.0),
            readability_score=data.get("readability_score", 0.0),
            comparison_difficulty=data.get("comparison_difficulty", 0.0),
            rare_token_density=data.get("rare_token_density", 0.0),
            entity_density=data.get("entity_density", 0.0),
            numeric_density=data.get("numeric_density", 0.0),
            abbreviation_density=data.get("abbreviation_density", 0.0),
            sentence_complexity=data.get("sentence_complexity", 0.0),
            question_length_score=data.get("question_length_score", 0.0),
            token_diversity=data.get("token_diversity", 0.0),
            confidence_estimate=data.get("confidence_estimate", 1.0),
            risk_score=data.get("risk_score", 0.0),
            reasoning_summary=data.get("reasoning_summary", ""),
            processing_time=data.get("processing_time", 0.0),
            version=data.get("version", "1.0.0"),
        )
