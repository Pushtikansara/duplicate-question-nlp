from __future__ import annotations

from enum import Enum

from duplicate_question_app._memory.interfaces import MemoryQuery


class RetrievalStrategy(Enum):
    EXACT = "exact"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    GRAPH = "graph"
    SIMILARITY = "similarity"


_STRATEGY_MAP = {
    "exact": RetrievalStrategy.EXACT,
    "semantic": RetrievalStrategy.SEMANTIC,
    "hybrid": RetrievalStrategy.HYBRID,
    "graph": RetrievalStrategy.GRAPH,
    "similarity": RetrievalStrategy.SIMILARITY,
}


class RetrievalStrategySelector:
    @staticmethod
    def select(query: MemoryQuery) -> RetrievalStrategy:
        qt = query.query_type.lower()
        return _STRATEGY_MAP.get(qt, RetrievalStrategy.EXACT)

    @staticmethod
    def get_retrieval_function(strategy: RetrievalStrategy):
        strategies = {
            RetrievalStrategy.EXACT: "exact_retrieval",
            RetrievalStrategy.SEMANTIC: "semantic_retrieval",
            RetrievalStrategy.HYBRID: "hybrid_retrieval",
            RetrievalStrategy.GRAPH: "graph_retrieval",
            RetrievalStrategy.SIMILARITY: "similarity_retrieval",
        }
        return strategies.get(strategy, "exact_retrieval")
