from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ares.query_understanding.complexity_models import ComplexityAnalysis
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.relationship_models import RelationshipAnalysis
from ares.query_understanding.type_models import QuestionTypeResult


@dataclass
class QuestionSimilarityFeatures:
    length_difference: int = 0
    word_overlap_ratio: float = 0.0
    char_overlap_ratio: float = 0.0
    unique_word_ratio: float = 0.0
    question_ratio: float = 0.0
    stopword_overlap_ratio: float = 0.0
    punctuation_similarity: float = 0.0
    capitalization_similarity: float = 0.0
    numeric_overlap: bool = False
    contains_same_url: bool = False
    contains_same_email: bool = False
    contains_same_code: bool = False


@dataclass
class QuestionMetadata:
    length: int = 0
    char_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    avg_word_length: float = 0.0
    language: str = "unknown"
    contains_numbers: bool = False
    contains_dates: bool = False
    contains_urls: bool = False
    contains_email: bool = False
    contains_code: bool = False
    contains_emoji: bool = False
    contains_special_chars: bool = False
    punctuation_count: int = 0
    capitalization_ratio: float = 0.0
    repeated_char_ratio: float = 0.0
    stopword_ratio: float = 0.0
    avg_token_length: float = 0.0
    numeric_count: int = 0
    symbol_count: int = 0
    whitespace_count: int = 0
    uppercase_word_ratio: float = 0.0
    lowercase_word_ratio: float = 0.0


@dataclass
class TokenStatistics:
    total_tokens: int = 0
    unique_tokens: int = 0
    avg_token_length: float = 0.0
    min_token_length: int = 0
    max_token_length: int = 0
    token_length_std: float = 0.0


@dataclass
class SentenceStatistics:
    total_sentences: int = 0
    avg_sentence_length_words: float = 0.0
    min_sentence_length: int = 0
    max_sentence_length: int = 0
    sentence_length_std: float = 0.0


@dataclass
class ReadabilityMetrics:
    flesch_reading_ease: float = 0.0
    avg_syllables_per_word: float = 0.0
    complex_word_count: int = 0
    complex_word_ratio: float = 0.0


@dataclass
class ComplexityScore:
    overall: float = 0.0
    lexical: float = 0.0
    syntactic: float = 0.0
    semantic: float = 0.0
    technical: float = 0.0


@dataclass
class QueryAnalysis:
    original_question_1: str = ""
    original_question_2: str = ""
    normalized_question_1: str = ""
    normalized_question_2: str = ""

    metadata_1: QuestionMetadata = field(default_factory=QuestionMetadata)
    metadata_2: QuestionMetadata = field(default_factory=QuestionMetadata)

    similarity: QuestionSimilarityFeatures = field(default_factory=QuestionSimilarityFeatures)

    token_stats_1: TokenStatistics = field(default_factory=TokenStatistics)
    token_stats_2: TokenStatistics = field(default_factory=TokenStatistics)

    sentence_stats_1: SentenceStatistics = field(default_factory=SentenceStatistics)
    sentence_stats_2: SentenceStatistics = field(default_factory=SentenceStatistics)

    readability_1: ReadabilityMetrics = field(default_factory=ReadabilityMetrics)
    readability_2: ReadabilityMetrics = field(default_factory=ReadabilityMetrics)

    complexity_1: ComplexityScore = field(default_factory=ComplexityScore)
    complexity_2: ComplexityScore = field(default_factory=ComplexityScore)

    confidence: float = 1.0
    timestamp: str = ""
    processing_time_ms: float = 0.0
    version: str = "1.0.0"

    question_type: QuestionTypeResult = field(default_factory=QuestionTypeResult)

    entity_analysis: EntityResult = field(default_factory=EntityResult)

    relationship_analysis: RelationshipAnalysis = field(default_factory=RelationshipAnalysis)

    complexity_analysis: ComplexityAnalysis = field(default_factory=ComplexityAnalysis)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["question_type"] = self.question_type.to_dict()
        d["entity_analysis"] = self.entity_analysis.to_dict()
        d["relationship_analysis"] = self.relationship_analysis.to_dict()
        d["complexity_analysis"] = self.complexity_analysis.to_dict()
        return d

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryAnalysis:
        similarity = QuestionSimilarityFeatures(**data.get("similarity", {}))
        question_type = QuestionTypeResult.from_dict(data.get("question_type", {}))
        entity_analysis = EntityResult.from_dict(data.get("entity_analysis", {}))
        relationship_analysis = RelationshipAnalysis.from_dict(data.get("relationship_analysis", {}))
        complexity_analysis = ComplexityAnalysis.from_dict(data.get("complexity_analysis", {}))
        metadata_1 = QuestionMetadata(**data.get("metadata_1", {}))
        metadata_2 = QuestionMetadata(**data.get("metadata_2", {}))
        token_stats_1 = TokenStatistics(**data.get("token_stats_1", {}))
        token_stats_2 = TokenStatistics(**data.get("token_stats_2", {}))
        sentence_stats_1 = SentenceStatistics(**data.get("sentence_stats_1", {}))
        sentence_stats_2 = SentenceStatistics(**data.get("sentence_stats_2", {}))
        readability_1 = ReadabilityMetrics(**data.get("readability_1", {}))
        readability_2 = ReadabilityMetrics(**data.get("readability_2", {}))
        complexity_1 = ComplexityScore(**data.get("complexity_1", {}))
        complexity_2 = ComplexityScore(**data.get("complexity_2", {}))

        return cls(
            original_question_1=data.get("original_question_1", ""),
            original_question_2=data.get("original_question_2", ""),
            normalized_question_1=data.get("normalized_question_1", ""),
            normalized_question_2=data.get("normalized_question_2", ""),
            metadata_1=metadata_1,
            metadata_2=metadata_2,
            similarity=similarity,
            token_stats_1=token_stats_1,
            token_stats_2=token_stats_2,
            sentence_stats_1=sentence_stats_1,
            sentence_stats_2=sentence_stats_2,
            readability_1=readability_1,
            readability_2=readability_2,
            complexity_1=complexity_1,
            complexity_2=complexity_2,
            confidence=data.get("confidence", 1.0),
            timestamp=data.get("timestamp", ""),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            version=data.get("version", "1.0.0"),
            question_type=question_type,
            entity_analysis=entity_analysis,
            relationship_analysis=relationship_analysis,
            complexity_analysis=complexity_analysis,
        )
