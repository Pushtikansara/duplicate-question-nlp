from __future__ import annotations

from ares.query_understanding.entity_detector import EntityDetector
from ares.query_understanding.relationship_detector import RelationshipDetector
from ares.query_understanding.relationship_models import RelationshipAnalysis


class RelationshipAnalyzer:
    version: str = "1.0.0"

    def __init__(self) -> None:
        self._detector = RelationshipDetector()
        self._entity_detector = EntityDetector()

    def analyze(
        self,
        question_1: str,
        question_2: str,
    ) -> RelationshipAnalysis:
        entity_result = self._entity_detector.detect(question_1, question_2)
        return self._detector.detect(
            question_1,
            question_2,
            entity_result=entity_result,
        )

    def compare(self, question_1: str, question_2: str) -> dict:
        analysis = self.analyze(question_1, question_2)
        return analysis.to_dict()
