from __future__ import annotations

import pytest

from ares.model_registry import (
    ModelCapabilities,
    ModelEntry,
    ModelHealth,
)
from ares.orchestration import (
    StrategyDefinition,
    StrategyRegistry,
    StrategySelector,
)
from ares.orchestration.constants import (
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
    STRATEGY_FAST_LEXICAL,
)
from ares.orchestration.exceptions import (
    DuplicateStrategyError,
    InvalidStrategyConfigurationError,
    ModelUnavailableError,
    StrategyNotFoundError,
    StrategyResolutionError,
)
from ares.query_understanding.router_models import RoutingDecision


def _entry(
    display_name: str,
    *,
    status: ModelHealth = ModelHealth.READY,
    capabilities: ModelCapabilities | None = None,
) -> ModelEntry:
    if capabilities is None:
        capabilities = ModelCapabilities(supports_batch=True)
        if "Cross-Encoder" in display_name:
            capabilities = ModelCapabilities(supports_batch=True, supports_cross_encoding=True)
    return ModelEntry(
        display_name=display_name,
        internal_id=display_name.lower().replace(" ", "_"),
        status=status,
        capabilities=capabilities,
    )


def _registry(monkeypatch: pytest.MonkeyPatch) -> StrategyRegistry:
    registry = StrategyRegistry.with_defaults()
    monkeypatch.setattr(
        "ares.orchestration.strategy_registry.find_entry",
        lambda model_name, paths=None: _entry(model_name),
    )
    return registry


class TestStrategyDefinition:
    def test_engine_config_conversion(self):
        definition = StrategyDefinition(name="test", model_name="Model A", threshold=0.7)
        config = definition.to_engine_configuration()
        assert config.model_name == "Model A"
        assert config.threshold == 0.7
        assert config.use_reflection is True

    def test_default_threshold_used_when_none(self):
        definition = StrategyDefinition(name="test", model_name="Model A")
        assert definition.to_engine_configuration().threshold == 0.5

    def test_from_mapping(self):
        definition = StrategyDefinition.from_mapping(
            "semantic",
            {
                "model": "Model B",
                "reflection": False,
                "semantic_validation": False,
                "enabled": True,
                "timeout_ms": 500,
                "cache_enabled": False,
                "priority": 3,
                "capabilities": ["embedding"],
            },
        )
        assert definition.name == "semantic"
        assert definition.model_name == "Model B"
        assert definition.use_reflection is False
        assert definition.timeout_ms == 500
        assert definition.cache_enabled is False
        assert definition.priority == 3
        assert definition.required_capabilities == frozenset({"embedding"})

    def test_from_mapping_missing_model(self):
        with pytest.raises(InvalidStrategyConfigurationError):
            StrategyDefinition.from_mapping("broken", {})

    def test_frozen(self):
        import dataclasses

        definition = StrategyDefinition(name="test", model_name="Model A")
        with pytest.raises(dataclasses.FrozenInstanceError):
            definition.name = "other"  # type: ignore[misc]


class TestStrategyRegistry:
    def test_register_and_resolve(self):
        registry = StrategyRegistry()
        registry.register(StrategyDefinition(name="fast", model_name="Model A"))
        definition = registry.resolve("fast")
        assert definition.model_name == "Model A"

    def test_duplicate_registration_raises(self):
        registry = StrategyRegistry()
        registry.register(StrategyDefinition(name="fast", model_name="Model A"))
        with pytest.raises(DuplicateStrategyError):
            registry.register(StrategyDefinition(name="fast", model_name="Model B"))

    def test_unknown_strategy_raises(self):
        registry = StrategyRegistry()
        with pytest.raises(StrategyNotFoundError):
            registry.resolve("does_not_exist")

    def test_list_strategies_preserves_order(self):
        registry = StrategyRegistry()
        registry.register(StrategyDefinition(name="b", model_name="M"))
        registry.register(StrategyDefinition(name="a", model_name="M"))
        assert registry.list_strategies() == ["b", "a"]

    def test_definitions(self):
        registry = StrategyRegistry.with_defaults()
        names = {definition.name for definition in registry.definitions()}
        assert names == {
            STRATEGY_FAST_LEXICAL,
            STRATEGY_BASELINE,
            STRATEGY_CROSS_ENCODER,
            STRATEGY_ENSEMBLE,
            STRATEGY_FALLBACK,
        }

    def test_contains(self):
        registry = StrategyRegistry.with_defaults()
        assert registry.contains("fallback") is True
        assert registry.contains("unknown") is False

    def test_len(self):
        registry = StrategyRegistry.with_defaults()
        assert len(registry) == 5

    def test_register_invalid_type(self):
        registry = StrategyRegistry()
        with pytest.raises(InvalidStrategyConfigurationError):
            registry.register("not_a_strategy")  # type: ignore[arg-type]

    def test_register_empty_name(self):
        registry = StrategyRegistry()
        with pytest.raises(InvalidStrategyConfigurationError):
            registry.register(StrategyDefinition(name="  ", model_name="Model A"))

    def test_from_config(self):
        config = {
            "strategy_defaults": {
                "fast_lexical": {"model": "Model A", "reflection": False, "capabilities": ["batch"]},
                "fallback": {"model": "Model B"},
            }
        }
        registry = StrategyRegistry.from_config(config)
        assert registry.list_strategies() == ["fast_lexical", "fallback"]
        assert registry.resolve("fast_lexical").use_reflection is False

    def test_from_config_bad_section(self):
        with pytest.raises(InvalidStrategyConfigurationError):
            StrategyRegistry.from_config({"strategy_defaults": ["not", "a", "mapping"]})

    def test_from_config_none_returns_empty(self):
        registry = StrategyRegistry.from_config(None)
        assert len(registry) == 0

    def test_with_defaults_mapping(self):
        registry = StrategyRegistry.with_defaults()
        assert registry.resolve(STRATEGY_FAST_LEXICAL).model_name == "TF-IDF + Logistic Regression (Week 2)"
        assert registry.resolve(STRATEGY_CROSS_ENCODER).model_name == "Cross-Encoder-Quora (Trained)"
        assert registry.resolve(STRATEGY_ENSEMBLE).model_name == "Semantic Ensemble"
        assert registry.resolve(STRATEGY_FALLBACK).model_name == "Improved DistilBERT (Week 4)"

    def test_validate_healthy(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(
            "ares.orchestration.strategy_registry.find_entry",
            lambda model_name, paths=None: _entry(model_name),
        )
        registry = StrategyRegistry.with_defaults()
        assert registry.validate() == []

    def test_validate_unknown_model(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("ares.orchestration.strategy_registry.find_entry", lambda model_name, paths=None: None)
        registry = StrategyRegistry.with_defaults()
        issues = registry.validate()
        assert len(issues) == 5
        assert all("not in the model registry" in issue for issue in issues)

    def test_validate_missing_status(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(
            "ares.orchestration.strategy_registry.find_entry",
            lambda model_name, paths=None: _entry(model_name, status=ModelHealth.MISSING),
        )
        registry = StrategyRegistry.with_defaults()
        assert any("missing" in issue for issue in registry.validate())

    def test_validate_capability_mismatch(self, monkeypatch: pytest.MonkeyPatch):
        entry = _entry("Cross-Encoder-Quora (Trained)", capabilities=ModelCapabilities(supports_batch=True))
        monkeypatch.setattr("ares.orchestration.strategy_registry.find_entry", lambda model_name, paths=None: entry)
        registry = StrategyRegistry.with_defaults()
        issues = registry.validate()
        assert any("cross_encoding" in issue for issue in issues)


class TestStrategySelector:
    def test_resolve_every_strategy(self, monkeypatch: pytest.MonkeyPatch):
        registry = _registry(monkeypatch)
        selector = StrategySelector(registry)
        for name in registry.list_strategies():
            decision = RoutingDecision(selected_strategy=name)
            config = selector.resolve(decision)
            assert config.model_name == registry.resolve(name).model_name
            assert isinstance(config.threshold, float)

    def test_deterministic_resolution(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        decision = RoutingDecision(selected_strategy="cross_encoder")
        first = selector.resolve(decision)
        second = selector.resolve(decision)
        assert first == second

    def test_user_model_override(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        from ares.orchestration import RequestParams

        config = selector.resolve(
            RoutingDecision(selected_strategy="fast_lexical"),
            RequestParams(model="Semantic Ensemble"),
        )
        assert config.model_name == "Semantic Ensemble"

    def test_user_threshold_override(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        from ares.orchestration import RequestParams

        config = selector.resolve(
            RoutingDecision(selected_strategy="fast_lexical"),
            RequestParams(threshold=0.9),
        )
        assert config.threshold == 0.9

    def test_user_reflection_override(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        from ares.orchestration import RequestParams

        config = selector.resolve(
            RoutingDecision(selected_strategy="fast_lexical"),
            RequestParams(reflect=True),
        )
        assert config.use_reflection is True

    def test_strategy_default_reflection(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        config = selector.resolve(RoutingDecision(selected_strategy="fast_lexical"))
        assert config.use_reflection is False

    def test_unknown_strategy(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        with pytest.raises(StrategyNotFoundError):
            selector.resolve(RoutingDecision(selected_strategy="nope"))

    def test_disabled_strategy(self, monkeypatch: pytest.MonkeyPatch):
        registry = StrategyRegistry([StrategyDefinition(name="offline", model_name="Model A", enabled=False)])
        monkeypatch.setattr(
            "ares.orchestration.strategy_registry.find_entry",
            lambda model_name, paths=None: _entry(model_name),
        )
        selector = StrategySelector(registry)
        with pytest.raises(StrategyResolutionError):
            selector.resolve(RoutingDecision(selected_strategy="offline"))

    def test_missing_model_raises(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("ares.orchestration.strategy_registry.find_entry", lambda model_name, paths=None: None)
        selector = StrategySelector(StrategyRegistry.with_defaults())
        with pytest.raises(ModelUnavailableError):
            selector.resolve(RoutingDecision(selected_strategy="fallback"))

    def test_missing_status_raises(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(
            "ares.orchestration.strategy_registry.find_entry",
            lambda model_name, paths=None: _entry(model_name, status=ModelHealth.MISSING),
        )
        selector = StrategySelector(StrategyRegistry.with_defaults())
        with pytest.raises(ModelUnavailableError):
            selector.resolve(RoutingDecision(selected_strategy="fallback"))

    def test_capability_mismatch_raises(self, monkeypatch: pytest.MonkeyPatch):
        entry = _entry("Cross-Encoder-Quora (Trained)", capabilities=ModelCapabilities(supports_batch=True))
        monkeypatch.setattr("ares.orchestration.strategy_registry.find_entry", lambda model_name, paths=None: entry)
        selector = StrategySelector(StrategyRegistry.with_defaults())
        with pytest.raises(StrategyResolutionError):
            selector.resolve(RoutingDecision(selected_strategy="cross_encoder"))

    def test_none_routing_decision(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        with pytest.raises(StrategyResolutionError):
            selector.resolve(None)

    def test_invalid_routing_decision_type(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        with pytest.raises(StrategyResolutionError):
            selector.resolve(42)  # type: ignore[arg-type]

    def test_empty_selected_strategy(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        with pytest.raises(StrategyResolutionError):
            selector.resolve(RoutingDecision(selected_strategy=""))

    def test_mapping_routing_decision(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        config = selector.resolve({"selected_strategy": "ensemble"})
        assert config.model_name == "Semantic Ensemble"

    def test_malformed_mapping(self, monkeypatch: pytest.MonkeyPatch):
        selector = StrategySelector(_registry(monkeypatch))
        with pytest.raises(StrategyResolutionError):
            selector.resolve({"selected_strategy": {"not": "a string"}})


class TestIntegration:
    def test_routing_decision_to_engine_config(self, monkeypatch: pytest.MonkeyPatch):
        registry = _registry(monkeypatch)
        selector = StrategySelector(registry)
        decision = RoutingDecision(
            selected_strategy=STRATEGY_CROSS_ENCODER,
            confidence=0.9,
            reason_codes=["high_ambiguity"],
            risk_level="high",
        )
        config = selector.resolve(decision, None)
        assert config.model_name == "Cross-Encoder-Quora (Trained)"
        assert config.use_reflection is True

    def test_config_driven_registry_resolves(self, monkeypatch: pytest.MonkeyPatch):
        from ares.orchestration.config_loader import build_strategy_registry

        registry = build_strategy_registry()
        monkeypatch.setattr(
            "ares.orchestration.strategy_registry.find_entry",
            lambda model_name, paths=None: _entry(model_name),
        )
        selector = StrategySelector(registry)
        config = selector.resolve(RoutingDecision(selected_strategy="fast_lexical"))
        assert config.model_name == "TF-IDF + Logistic Regression (Week 2)"
        assert config.use_reflection is False
