from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ares.model_registry import ModelHealth, find_entry
from ares.orchestration.config import EngineConfiguration
from ares.orchestration.constants import (
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_THRESHOLD,
    STRATEGY_BASELINE,
    STRATEGY_CROSS_ENCODER,
    STRATEGY_ENSEMBLE,
    STRATEGY_FALLBACK,
    STRATEGY_FAST_LEXICAL,
)
from ares.orchestration.context import RequestParams
from ares.orchestration.exceptions import (
    DuplicateStrategyError,
    InvalidStrategyConfigurationError,
    ModelUnavailableError,
    StrategyNotFoundError,
    StrategyResolutionError,
)
from ares.query_understanding.router_models import RoutingDecision

#: Capability keys accepted in ``StrategyDefinition.required_capabilities``
#: mapped to the corresponding attribute on the model registry's
#: ``ModelCapabilities``.
CAPABILITY_ATTRIBUTES: dict[str, str] = {
    "batch": "supports_batch",
    "stream": "supports_stream",
    "embedding": "supports_embedding",
    "cross_encoding": "supports_cross_encoding",
    "calibration": "supports_calibration",
    "explainability": "supports_explainability",
    "gpu": "supports_gpu",
    "quantization": "supports_quantization",
}


@dataclass(frozen=True)
class StrategyDefinition:
    """Executable configuration behind one routing strategy.

    ``name`` and ``model_name`` are required; all other fields carry the
    defaults established by the Phase 13 architecture. ``enabled`` may be
    flipped per environment without removing the strategy from the catalog.
    """

    name: str
    model_name: str
    threshold: float | None = None
    use_reflection: bool = True
    use_semantic_validation: bool = True
    enabled: bool = True
    timeout_ms: float | None = None
    cache_enabled: bool = True
    priority: int = 0
    required_capabilities: frozenset[str] = field(default_factory=frozenset)

    def to_engine_configuration(self) -> EngineConfiguration:
        return EngineConfiguration(
            model_name=self.model_name,
            threshold=self.threshold if self.threshold is not None else DEFAULT_THRESHOLD,
            use_reflection=self.use_reflection,
            use_semantic_validation=self.use_semantic_validation,
        )

    @classmethod
    def from_mapping(cls, name: str, data: Mapping[str, Any]) -> StrategyDefinition:
        """Build a definition from a configuration mapping.

        Accepts the documented keys: ``model`` (required), ``threshold``,
        ``reflection``, ``semantic_validation``, ``enabled``, ``timeout_ms``,
        ``cache_enabled``, ``priority``, ``capabilities``.
        """
        model_name = data.get("model")
        if not isinstance(model_name, str) or not model_name.strip():
            raise InvalidStrategyConfigurationError(f"Strategy '{name}' is missing a valid 'model' entry")
        capabilities = data.get("capabilities", [])
        if capabilities is None:
            capabilities = []
        return cls(
            name=name,
            model_name=model_name,
            threshold=data.get("threshold"),
            use_reflection=bool(data.get("reflection", True)),
            use_semantic_validation=bool(data.get("semantic_validation", True)),
            enabled=bool(data.get("enabled", True)),
            timeout_ms=data.get("timeout_ms"),
            cache_enabled=bool(data.get("cache_enabled", True)),
            priority=int(data.get("priority", 0)),
            required_capabilities=frozenset(capabilities),
        )


class StrategyRegistry:
    """Catalog of strategy definitions, loadable from configuration.

    The registry is the single source of truth for the strategy → model
    mapping. It is intentionally not a hardcoded module-level dictionary:
    definitions are registered programmatically or loaded from
    ``configs/orchestration.yaml``.
    """

    def __init__(self, strategies: Iterable[StrategyDefinition] | None = None) -> None:
        self._strategies: dict[str, StrategyDefinition] = {}
        if strategies:
            for strategy in strategies:
                self.register(strategy)

    def register(self, strategy: StrategyDefinition) -> None:
        if not isinstance(strategy, StrategyDefinition):
            raise InvalidStrategyConfigurationError("Only StrategyDefinition instances can be registered")
        if not strategy.name or not strategy.name.strip():
            raise InvalidStrategyConfigurationError("Strategy name must be a non-empty string")
        if strategy.name in self._strategies:
            raise DuplicateStrategyError(f"Strategy already registered: '{strategy.name}'")
        self._strategies[strategy.name] = strategy

    def resolve(self, name: str) -> StrategyDefinition:
        if name not in self._strategies:
            raise StrategyNotFoundError(f"Unknown strategy: '{name}'")
        return self._strategies[name]

    def contains(self, name: str) -> bool:
        return name in self._strategies

    def list_strategies(self) -> list[str]:
        return list(self._strategies)

    def definitions(self) -> list[StrategyDefinition]:
        return list(self._strategies.values())

    def validate(self, paths: Any = None) -> list[str]:
        """Validate every registered strategy against the model registry.

        Returns a list of human-readable issues (empty when healthy). Issues
        cover unknown models, models that are not ready, and capability
        mismatches. Resolution itself raises the Phase 13 exceptions.
        """
        issues: list[str] = []
        for name, strategy in self._strategies.items():
            entry = find_entry(strategy.model_name, paths)
            if entry is None:
                issues.append(f"Strategy '{name}': model '{strategy.model_name}' is not in the model registry")
                continue
            if entry.status in (ModelHealth.MISSING, ModelHealth.DISABLED):
                issues.append(f"Strategy '{name}': model '{strategy.model_name}' is {entry.status.value}")
            unsupported = _unsupported_capabilities(strategy.required_capabilities, entry)
            if unsupported:
                issues.append(
                    f"Strategy '{name}': model '{strategy.model_name}' lacks capabilities: {sorted(unsupported)}"
                )
        return issues

    def __len__(self) -> int:
        return len(self._strategies)

    @classmethod
    def from_config(cls, config: Mapping[str, Any] | None) -> StrategyRegistry:
        """Build a registry from the ``strategy_defaults`` section of
        ``configs/orchestration.yaml``.
        """
        if not config:
            return cls()
        defaults = config.get("strategy_defaults") or {}
        if not isinstance(defaults, Mapping):
            raise InvalidStrategyConfigurationError("'strategy_defaults' must be a mapping of strategy name to config")
        definitions = [StrategyDefinition.from_mapping(name, data) for name, data in defaults.items()]
        return cls(definitions)

    @classmethod
    def with_defaults(cls) -> StrategyRegistry:
        """Registry pre-populated with the Phase 13 default strategy set.

        Used when no configuration file is present. The mapping mirrors the
        approved architecture (fast path → classical models, semantic path →
        cross encoder/ensemble, fallback → default engine model).
        """
        return cls(
            [
                StrategyDefinition(
                    name=STRATEGY_FAST_LEXICAL,
                    model_name="TF-IDF + Logistic Regression (Week 2)",
                    use_reflection=False,
                    use_semantic_validation=False,
                    priority=100,
                    timeout_ms=1000.0,
                    required_capabilities=frozenset({"batch"}),
                ),
                StrategyDefinition(
                    name=STRATEGY_BASELINE,
                    model_name="TF-IDF + Linear SVM (Week 2)",
                    use_reflection=False,
                    use_semantic_validation=False,
                    priority=90,
                    timeout_ms=1000.0,
                    required_capabilities=frozenset({"batch"}),
                ),
                StrategyDefinition(
                    name=STRATEGY_CROSS_ENCODER,
                    model_name="Cross-Encoder-Quora (Trained)",
                    priority=80,
                    required_capabilities=frozenset({"cross_encoding"}),
                ),
                StrategyDefinition(
                    name=STRATEGY_ENSEMBLE,
                    model_name="Semantic Ensemble",
                    priority=70,
                ),
                StrategyDefinition(
                    name=STRATEGY_FALLBACK,
                    model_name=DEFAULT_FALLBACK_MODEL,
                    priority=10,
                ),
            ]
        )


def _unsupported_capabilities(required: frozenset[str], entry: Any) -> list[str]:
    capabilities = getattr(entry, "capabilities", None)
    if capabilities is None:
        return sorted(required)
    unsupported: list[str] = []
    for capability in required:
        attribute = CAPABILITY_ATTRIBUTES.get(capability)
        if attribute is None or not bool(getattr(capabilities, attribute, False)):
            unsupported.append(capability)
    return unsupported


class StrategySelector:
    """Deterministically translates a routing decision into an executable
    engine configuration.

    Pure function of ``(RoutingDecision, RequestParams, registered
    strategies, model registry)`` — no LLM, no randomness, no network calls.
    """

    def __init__(self, registry: StrategyRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> StrategyRegistry:
        return self._registry

    def resolve(
        self,
        routing_decision: RoutingDecision | Mapping[str, Any] | None,
        request_params: RequestParams | None = None,
        paths: Any = None,
    ) -> EngineConfiguration:
        decision = self._coerce_routing_decision(routing_decision)
        if not decision.selected_strategy:
            raise StrategyResolutionError("Routing decision carries no selected strategy")

        definition = self._registry.resolve(decision.selected_strategy)
        if not definition.enabled:
            raise StrategyResolutionError(f"Strategy '{definition.name}' is disabled")

        model_name = self._resolve_model(definition, request_params, paths)
        threshold = self._resolve_threshold(definition, request_params)
        use_reflection = self._resolve_reflection(definition, request_params)

        return EngineConfiguration(
            model_name=model_name,
            threshold=threshold,
            use_reflection=use_reflection,
            use_semantic_validation=definition.use_semantic_validation,
        )

    def _coerce_routing_decision(self, routing_decision: RoutingDecision | Mapping[str, Any] | None) -> RoutingDecision:
        if routing_decision is None:
            raise StrategyResolutionError("No routing decision provided")
        if isinstance(routing_decision, RoutingDecision):
            return routing_decision
        if isinstance(routing_decision, Mapping):
            try:
                decision = RoutingDecision.from_dict(dict(routing_decision))
            except (TypeError, ValueError) as exc:
                raise StrategyResolutionError(f"Malformed routing decision: {exc}") from exc
            if not isinstance(decision.selected_strategy, str):
                raise StrategyResolutionError("Malformed routing decision: 'selected_strategy' must be a string")
            return decision
        raise StrategyResolutionError(
            f"Routing decision must be a RoutingDecision or mapping, got {type(routing_decision).__name__}"
        )

    def _resolve_model(self, definition: StrategyDefinition, request_params: RequestParams | None, paths: Any) -> str:
        model_name = (
            request_params.model.strip()
            if request_params is not None and request_params.model and request_params.model.strip()
            else definition.model_name
        )
        entry = find_entry(model_name, paths)
        if entry is None:
            raise ModelUnavailableError(f"Model '{model_name}' is not in the model registry")
        if entry.status in (ModelHealth.MISSING, ModelHealth.DISABLED):
            raise ModelUnavailableError(
                f"Model '{model_name}' is {entry.status.value} and cannot be used for strategy '{definition.name}'"
            )
        unsupported = _unsupported_capabilities(definition.required_capabilities, entry)
        if unsupported:
            raise StrategyResolutionError(
                f"Model '{model_name}' cannot serve strategy '{definition.name}': "
                f"missing capabilities {sorted(unsupported)}"
            )
        return model_name

    @staticmethod
    def _resolve_threshold(definition: StrategyDefinition, request_params: RequestParams | None) -> float:
        if request_params is not None and request_params.threshold is not None:
            return request_params.threshold
        if definition.threshold is not None:
            return definition.threshold
        return DEFAULT_THRESHOLD

    @staticmethod
    def _resolve_reflection(definition: StrategyDefinition, request_params: RequestParams | None) -> bool:
        if request_params is not None and request_params.reflect is not None:
            return request_params.reflect
        return definition.use_reflection
