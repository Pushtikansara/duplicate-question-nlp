from __future__ import annotations

from typing import Any

from ares.query_understanding.query_analyzer import QueryAnalyzer
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.utils import validate_input


class QueryPipeline:
    def __init__(self, analyzer: QueryAnalyzer | None = None):
        self.analyzer = analyzer or QueryAnalyzer()

    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        validate_input(question_1, question_2)
        return self.analyzer.analyze(question_1, question_2)

    def run_batch(self, pairs: list[tuple[str, str]]) -> list[QueryAnalysis]:
        return [self.run(q1, q2) for q1, q2 in pairs]

    def run_with_metadata(self, question_1: str, question_2: str, extra: dict[str, Any] | None = None) -> QueryAnalysis:
        result = self.run(question_1, question_2)
        if extra:
            for key, value in extra.items():
                if hasattr(result, key):
                    setattr(result, key, value)
        return result

    def to_dataframe(self, analyses: list[QueryAnalysis]) -> Any:
        try:
            import pandas as pd

            records = [a.to_dict() for a in analyses]
            df = pd.json_normalize(records, sep="_")
            return df
        except ImportError:
            return None
