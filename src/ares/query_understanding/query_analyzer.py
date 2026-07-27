from __future__ import annotations

import time
from datetime import datetime

from ares.query_understanding.entity_detector import EntityDetector
from ares.query_understanding.query_features import (
    extract_complexity,
    extract_question_metadata,
    extract_readability,
    extract_sentence_statistics,
    extract_similarity_features,
    extract_token_statistics,
)
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.question_type_detector import QuestionTypeDetector
from ares.query_understanding.utils import (
    detect_language,
    normalize_text,
    validate_input,
)


class QueryAnalyzer:
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._type_detector = QuestionTypeDetector()
        self._entity_detector = EntityDetector()

    def analyze(self, question_1: str, question_2: str) -> QueryAnalysis:
        start = time.time()
        try:
            validate_input(question_1, question_2)
        except (TypeError, ValueError):
            pass

        normalized_1 = normalize_text(question_1) if isinstance(question_1, str) else ""
        normalized_2 = normalize_text(question_2) if isinstance(question_2, str) else ""

        if not normalized_1 and not normalized_2:
            return QueryAnalysis(
                original_question_1=str(question_1) if not isinstance(question_1, str) else question_1,
                original_question_2=str(question_2) if not isinstance(question_2, str) else question_2,
                timestamp=datetime.utcnow().isoformat(),
                processing_time_ms=round((time.time() - start) * 1000, 2),
                version=self.version,
            )

        metadata_1 = extract_question_metadata(normalized_1)
        metadata_2 = extract_question_metadata(normalized_2)

        metadata_1.language = detect_language(question_1)
        metadata_2.language = detect_language(question_2)

        similarity = extract_similarity_features(normalized_1, normalized_2, metadata_1, metadata_2)

        token_stats_1 = extract_token_statistics(normalized_1)
        token_stats_2 = extract_token_statistics(normalized_2)

        sentence_stats_1 = extract_sentence_statistics(normalized_1)
        sentence_stats_2 = extract_sentence_statistics(normalized_2)

        readability_1 = extract_readability(normalized_1)
        readability_2 = extract_readability(normalized_2)

        complexity_1 = extract_complexity(metadata_1, readability_1)
        complexity_2 = extract_complexity(metadata_2, readability_2)

        question_type = self._type_detector.detect(
            question_1,
            question_2,
            normalized_1,
            normalized_2,
        )

        entity_analysis = self._entity_detector.detect(question_1, question_2)

        elapsed = round((time.time() - start) * 1000, 2)

        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            normalized_question_1=normalized_1,
            normalized_question_2=normalized_2,
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
            confidence=1.0,
            timestamp=datetime.utcnow().isoformat(),
            processing_time_ms=elapsed,
            version=self.version,
            question_type=question_type,
            entity_analysis=entity_analysis,
        )
