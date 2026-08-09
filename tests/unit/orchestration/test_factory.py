from __future__ import annotations

from typing import Any

from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.constants import (
    DEFAULT_STAGE_ORDER,
    STAGE_INPUT_VALIDATION,
    STAGE_PREDICTION,
    STAGE_QUERY_UNDERSTANDING,
    STAGE_RESULT_ENRICHMENT,
    STAGE_STRATEGY_SELECTION,
)
from ares.orchestration.factory import build_default_stage_registry
from ares.orchestration.strategy_registry import StrategyRegistry, StrategySelector
from ares.query_understanding.query_models import QueryAnalysis
from ares.query_understanding.query_pipeline import QueryPipeline
from ares.query_understanding.router_models import RoutingDecision


class _StubEngine:
    def predict(self, question1: str, question2: str, **kwargs: Any) -> Any:
        return "predicted"


class _StubQueryPipeline(QueryPipeline):
    def run(self, question_1: str, question_2: str) -> QueryAnalysis:
        return QueryAnalysis(
            original_question_1=question_1,
            original_question_2=question_2,
            routing_decision=RoutingDecision(selected_strategy="fast_lexical"),
        )


def _registry(**kwargs: Any):
    return build_default_stage_registry(
        _StubEngine(),
        _StubQueryPipeline(),
        StrategySelector(StrategyRegistry.with_defaults()),
        **kwargs,
    )


class TestDefaultStageRegistry:
    def test_default_registry_has_five_stages_in_documented_order(self):
        registry = _registry()
        names = [s.name for s in registry.ordered_stages()]
        assert names == DEFAULT_STAGE_ORDER

    def test_registry_resolves_each_default_stage(self):
        registry = _registry()
        for name in DEFAULT_STAGE_ORDER:
            assert registry.resolve(name).name == name

    def test_stage_config_disables_stage(self):
        registry = _registry(
            stage_config={STAGE_QUERY_UNDERSTANDING: {"enabled": False}},
        )
        names = [s.name for s in registry.ordered_stages()]
        assert names == [
            STAGE_INPUT_VALIDATION,
            STAGE_STRATEGY_SELECTION,
            STAGE_PREDICTION,
            STAGE_RESULT_ENRICHMENT,
        ]

    def test_stage_config_reorders_stages(self):
        registry = _registry(
            stage_config={
                STAGE_PREDICTION: {"order": 1},
                STAGE_INPUT_VALIDATION: {"order": 2},
            },
        )
        names = [s.name for s in registry.ordered_stages()]
        assert names[0] == STAGE_PREDICTION
        assert names[1] == STAGE_INPUT_VALIDATION

    def test_cache_provider_wired_into_query_understanding_stage(self):
        cache = InMemoryCacheProvider()
        registry = _registry(cache_provider=cache)
        stage = registry.resolve(STAGE_QUERY_UNDERSTANDING)
        assert stage._cache_provider is cache

    def test_disabling_prediction_keeps_other_stages(self):
        registry = _registry(stage_config={STAGE_PREDICTION: {"enabled": False}})
        names = [s.name for s in registry.ordered_stages()]
        assert STAGE_PREDICTION not in names
        assert names == [
            STAGE_INPUT_VALIDATION,
            STAGE_QUERY_UNDERSTANDING,
            STAGE_STRATEGY_SELECTION,
            STAGE_RESULT_ENRICHMENT,
        ]
