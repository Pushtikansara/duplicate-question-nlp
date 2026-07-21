"""CognitiveRepresentation — the universal output of the Cognitive Perception Engine.

This is the ONLY data structure that future ARES engines receive as input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass
class Token:
    text: str
    start: int
    end: int
    pos_tag: str | None = None
    is_stopword: bool = False
    lemma: str | None = None


@dataclass
class Sentence:
    text: str
    start: int
    end: int
    tokens: list[Token] = field(default_factory=list)
    language: str | None = None


@dataclass
class Entity:
    entity_type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Negation:
    text: str
    start: int
    end: int
    negation_type: str
    scope: str
    confidence: float
    target: str | None = None


@dataclass
class LinguisticFeatures:
    entities: list[Entity] = field(default_factory=list)
    negations: list[Negation] = field(default_factory=list)
    intent: str | None = None
    intent_confidence: float = 0.0
    lexical_density: float = 0.0
    subjectivity: float = 0.0


@dataclass
class Metadata:
    length: int = 0
    char_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    question_type: str | None = None
    has_question_mark: bool = False
    has_exclamation: bool = False
    has_code: bool = False
    has_url: bool = False
    has_email: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CognitiveRepresentation:
    raw_text: str
    normalized_text: str
    language: str
    language_confidence: float
    tokens: list[Token]
    sentences: list[Sentence]
    linguistic: LinguisticFeatures
    metadata: Metadata
    validation: ValidationReport
    linguistic_profile: Any = None
    semantic_representation: Any = None
    pipeline_version: str = "1.2.0"
    processing_time_ms: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base = {
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "language": self.language,
            "language_confidence": self.language_confidence,
            "tokens": [{"text": t.text, "start": t.start, "end": t.end} for t in self.tokens],
            "sentences": [
                {"text": s.text, "start": s.start, "end": s.end, "language": s.language} for s in self.sentences
            ],
            "linguistic": {
                "entities": [
                    {"type": e.entity_type, "value": e.value, "confidence": e.confidence}
                    for e in self.linguistic.entities
                ],
                "negations": [
                    {"text": n.text, "type": n.negation_type, "scope": n.scope} for n in self.linguistic.negations
                ],
                "intent": self.linguistic.intent,
                "intent_confidence": self.linguistic.intent_confidence,
                "lexical_density": self.linguistic.lexical_density,
                "subjectivity": self.linguistic.subjectivity,
            },
            "metadata": {
                "length": self.metadata.length,
                "char_count": self.metadata.char_count,
                "word_count": self.metadata.word_count,
                "sentence_count": self.metadata.sentence_count,
                "question_type": self.metadata.question_type,
                "has_question_mark": self.metadata.has_question_mark,
                "has_exclamation": self.metadata.has_exclamation,
                "has_code": self.metadata.has_code,
                "has_url": self.metadata.has_url,
                "has_email": self.metadata.has_email,
            },
            "validation": {
                "valid": self.validation.valid,
                "errors": self.validation.errors,
                "warnings": self.validation.warnings,
            },
            "pipeline_version": self.pipeline_version,
            "processing_time_ms": self.processing_time_ms,
        }
        if self.linguistic_profile is not None:
            try:
                base["linguistic_profile"] = self.linguistic_profile.to_dict()
            except Exception:
                base["linguistic_profile"] = str(self.linguistic_profile)
        if self.semantic_representation is not None:
            try:
                base["semantic_representation"] = self.semantic_representation.to_dict()
            except Exception:
                base["semantic_representation"] = str(self.semantic_representation)
        return base
