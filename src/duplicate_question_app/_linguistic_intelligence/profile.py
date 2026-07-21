"""LinguisticProfile — the unified rich linguistic profile embedded in CognitiveRepresentation.

Every analysis produced by the Linguistic Intelligence Layer lives here.
Future engines consume ONLY CognitiveRepresentation, never calling analyzers directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenStatistics:
    total: int = 0
    unique: int = 0
    stopword_count: int = 0
    punctuation_count: int = 0
    numeric_count: int = 0
    avg_token_length: float = 0.0
    type_token_ratio: float = 0.0


@dataclass
class SentenceStatistics:
    total: int = 0
    avg_sentence_length: float = 0.0
    min_sentence_length: int = 0
    max_sentence_length: int = 0
    question_sentences: int = 0
    exclamatory_sentences: int = 0


@dataclass
class ComplexityScore:
    overall: float = 0.0
    vocabulary_complexity: float = 0.0
    syntactic_complexity: float = 0.0
    sentence_complexity: float = 0.0
    readability: float = 0.0
    flesch_reading_ease: float = 0.0
    avg_sentence_words: float = 0.0
    long_word_ratio: float = 0.0
    polysyllable_count: int = 0


@dataclass
class ReadabilityScore:
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    coleman_liau_index: float = 0.0
    avg: float = 0.0


@dataclass
class Keyword:
    word: str
    score: float
    frequency: int = 1
    tfidf_score: float = 0.0
    is_noun: bool = False
    is_verb: bool = False
    is_entity: bool = False


@dataclass
class LexicalFeatures:
    lexical_density: float = 0.0
    lexical_diversity: float = 0.0
    noun_count: int = 0
    verb_count: int = 0
    content_word_count: int = 0
    function_word_count: int = 0
    unique_nouns: list[str] = field(default_factory=list)
    unique_verbs: list[str] = field(default_factory=list)


@dataclass
class SyntacticFeatures:
    sentence_types: dict[str, int] = field(default_factory=dict)
    avg_phrase_length: float = 0.0
    subordinate_clause_count: int = 0
    coord_conjunction_count: int = 0


@dataclass
class DependencyFeatures:
    has_nsubj: bool = False
    has_dobj: bool = False
    has_amod: bool = False
    dependency_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class AnalysisConfidence:
    overall: float = 0.0
    language: float = 0.0
    intent: float = 0.0
    entities: float = 0.0
    keyword: float = 0.0
    question_type: float = 0.0
    complexity: float = 0.0
    domain: float = 0.0
    per_analyzer: dict[str, float] = field(default_factory=dict)


@dataclass
class QualityMetricsData:
    coverage: float = 0.0
    completeness: float = 0.0
    confidence: float = 0.0
    latency_ms: float = 0.0
    processing_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    quality_score: float = 0.0
    per_metric: dict[str, float] = field(default_factory=dict)


@dataclass
class LinguisticProfile:
    language: str = ""
    language_confidence: float = 0.0
    intent: str | None = None
    intent_confidence: float = 0.0
    question_type: str | None = None
    question_class: str | None = None
    entities: list[dict[str, Any]] = field(default_factory=list)
    entity_count: int = 0
    keywords: list[Keyword] = field(default_factory=list)
    keyword_scores: dict[str, float] = field(default_factory=dict)
    negation: bool = False
    negation_count: int = 0
    contradiction: bool = False
    contradiction_score: float = 0.0
    lexical_features: LexicalFeatures = field(default_factory=LexicalFeatures)
    token_statistics: TokenStatistics = field(default_factory=TokenStatistics)
    sentence_statistics: SentenceStatistics = field(default_factory=SentenceStatistics)
    complexity: ComplexityScore = field(default_factory=ComplexityScore)
    readability: ReadabilityScore = field(default_factory=ReadabilityScore)
    domain: str | None = None
    domain_confidence: float = 0.0
    syntactic_features: SyntacticFeatures = field(default_factory=SyntacticFeatures)
    dependency_features: DependencyFeatures = field(default_factory=DependencyFeatures)
    quality_metrics: QualityMetricsData = field(default_factory=QualityMetricsData)
    analysis_confidence: AnalysisConfidence = field(default_factory=AnalysisConfidence)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "language_confidence": self.language_confidence,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "question_type": self.question_type,
            "question_class": self.question_class,
            "entities": self.entities,
            "entity_count": self.entity_count,
            "keywords": [{"word": k.word, "score": k.score, "frequency": k.frequency} for k in self.keywords],
            "keyword_scores": self.keyword_scores,
            "negation": self.negation,
            "negation_count": self.negation_count,
            "contradiction": self.contradiction,
            "contradiction_score": self.contradiction_score,
            "lexical_features": {
                "lexical_density": self.lexical_features.lexical_density,
                "lexical_diversity": self.lexical_features.lexical_diversity,
                "noun_count": self.lexical_features.noun_count,
                "verb_count": self.lexical_features.verb_count,
            },
            "token_statistics": {
                "total": self.token_statistics.total,
                "unique": self.token_statistics.unique,
                "type_token_ratio": self.token_statistics.type_token_ratio,
            },
            "sentence_statistics": {
                "total": self.sentence_statistics.total,
                "avg_sentence_length": self.sentence_statistics.avg_sentence_length,
            },
            "complexity": {
                "overall": self.complexity.overall,
                "readability": self.complexity.readability,
                "flesch_reading_ease": self.complexity.flesch_reading_ease,
                "avg_sentence_words": self.complexity.avg_sentence_words,
            },
            "readability": {
                "flesch_reading_ease": self.readability.flesch_reading_ease,
                "flesch_kincaid_grade": self.readability.flesch_kincaid_grade,
            },
            "domain": self.domain,
            "domain_confidence": self.domain_confidence,
            "quality_metrics": {
                "quality_score": self.quality_metrics.quality_score,
                "coverage": self.quality_metrics.coverage,
                "confidence": self.quality_metrics.confidence,
                "completeness": self.quality_metrics.completeness,
                "latency_ms": self.quality_metrics.latency_ms,
                "warnings": self.quality_metrics.warnings,
                "errors": self.quality_metrics.errors,
            },
            "analysis_confidence": {
                "overall": self.analysis_confidence.overall,
                "language": self.analysis_confidence.language,
                "intent": self.analysis_confidence.intent,
                "entities": self.analysis_confidence.entities,
                "per_analyzer": self.analysis_confidence.per_analyzer,
            },
        }
