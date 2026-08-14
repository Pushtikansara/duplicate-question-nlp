from __future__ import annotations

from typing import Any

from ares.adaptive.config_loader import AdaptiveRoutingConfig
from ares.adaptive.models import ModelProfile
from ares.model_registry import ModelBackend, ModelHealth, build_registry


class ModelProfileRegistry:
    """Discovers models through the existing ``ares.model_registry`` and
    exposes capability / cost metadata for the adaptive router.

    No model-specific routing logic lives here: profiles are derived from the
    registry plus optional ``model_profiles`` configuration (keyed by internal
    id), so future models only need registry/config entries.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        registry=None,
    ) -> None:
        self._config = AdaptiveRoutingConfig(config)
        self._overrides = self._config.model_profiles
        self._entries = registry if registry is not None else build_registry()
        self._profiles: dict[str, ModelProfile] | None = None

    def _build(self) -> dict[str, ModelProfile]:
        profiles: dict[str, ModelProfile] = {}
        for entry in self._entries:
            available = entry.status == ModelHealth.READY or entry.has_artifacts
            base = _base_profile(entry.internal_id, entry.display_name, entry.backend, available, entry.memory_usage_mb)
            override = self._overrides.get(entry.internal_id) or {}
            profiles[entry.internal_id] = _merge_profile(base, override)
        return profiles

    @property
    def profiles(self) -> dict[str, ModelProfile]:
        if self._profiles is None:
            self._profiles = self._build()
        return self._profiles

    def get(self, model_name: str) -> ModelProfile | None:
        for profile in self.profiles.values():
            if profile.model_name == model_name:
                return profile
        return self.profiles.get(model_name)

    def get_by_internal_id(self, internal_id: str) -> ModelProfile | None:
        return self.profiles.get(internal_id)

    def available(self) -> list[ModelProfile]:
        return [p for p in self.profiles.values() if p.available]

    def cheapest(self) -> ModelProfile | None:
        available = self.available()
        if not available:
            return None
        return min(available, key=lambda p: (p.computational_cost, p.expected_latency_ms))

    def strongest(self) -> ModelProfile | None:
        available = self.available()
        if not available:
            return None
        return max(available, key=lambda p: (p.expected_accuracy, -p.computational_cost))

    def list_model_names(self) -> list[str]:
        return [p.model_name for p in self.profiles.values() if p.available]

    def compute_cost(self, model_name: str) -> float:
        profile = self.get(model_name)
        return profile.computational_cost if profile is not None else 1.0


def _base_profile(
    internal_id: str,
    display_name: str,
    backend: ModelBackend,
    available: bool,
    memory_mb: float | None,
) -> ModelProfile:
    defaults = _BACKEND_DEFAULTS.get(backend.value) or _BACKEND_DEFAULTS.get("transformer")
    if defaults is None:
        defaults = {
            "tier": 1,
            "accuracy": 0.7,
            "latency_ms": 25.0,
            "cost": 1.0,
            "confidence_quality": 0.5,
            "reliability": 0.5,
            "fallback_priority": 5,
        }
    return ModelProfile(
        model_name=display_name,
        internal_id=internal_id,
        model_type=backend.value,
        capability_tier=defaults["tier"],
        expected_accuracy=defaults["accuracy"],
        expected_latency_ms=defaults["latency_ms"],
        computational_cost=defaults["cost"],
        memory_cost_mb=float(memory_mb or 0.0),
        confidence_quality=defaults["confidence_quality"],
        reliability=defaults["reliability"],
        fallback_priority=defaults["fallback_priority"],
        available=available,
    )


def _merge_profile(base: ModelProfile, override: dict[str, Any]) -> ModelProfile:
    if not override:
        return base
    fields = {
        "expected_accuracy": override.get("expected_accuracy", base.expected_accuracy),
        "expected_latency_ms": float(override.get("expected_latency_ms", base.expected_latency_ms)),
        "computational_cost": float(override.get("computational_cost", base.computational_cost)),
        "memory_cost_mb": float(override.get("memory_cost_mb", base.memory_cost_mb)),
        "confidence_quality": float(override.get("confidence_quality", base.confidence_quality)),
        "reliability": float(override.get("reliability", base.reliability)),
        "fallback_priority": int(override.get("fallback_priority", base.fallback_priority)),
        "capability_tier": str(override.get("capability_tier", base.capability_tier)),
    }
    return ModelProfile(
        model_name=base.model_name,
        internal_id=base.internal_id,
        model_type=base.model_type,
        capability_tier=fields["capability_tier"],
        expected_accuracy=fields["expected_accuracy"],
        expected_latency_ms=fields["expected_latency_ms"],
        computational_cost=fields["computational_cost"],
        memory_cost_mb=fields["memory_cost_mb"],
        confidence_quality=fields["confidence_quality"],
        reliability=fields["reliability"],
        fallback_priority=fields["fallback_priority"],
        supported_tasks=base.supported_tasks,
        available=base.available,
    )


_BACKEND_DEFAULTS: dict[str, dict[str, Any]] = {
    ModelBackend.CLASSICAL_ML.value: {
        "tier": "classical",
        "accuracy": 0.72,
        "latency_ms": 1.0,
        "cost": 1.0,
        "confidence_quality": 0.5,
        "reliability": 0.9,
        "fallback_priority": 4,
    },
    ModelBackend.TRANSFORMER.value: {
        "tier": "transformer",
        "accuracy": 0.82,
        "latency_ms": 3.5,
        "cost": 5.0,
        "confidence_quality": 0.65,
        "reliability": 0.85,
        "fallback_priority": 3,
    },
    ModelBackend.BI_ENCODER.value: {
        "tier": "bi-encoder",
        "accuracy": 0.80,
        "latency_ms": 5.0,
        "cost": 4.0,
        "confidence_quality": 0.6,
        "reliability": 0.85,
        "fallback_priority": 3,
    },
    ModelBackend.CROSS_ENCODER.value: {
        "tier": "cross-encoder",
        "accuracy": 0.87,
        "latency_ms": 21.0,
        "cost": 10.0,
        "confidence_quality": 0.8,
        "reliability": 0.8,
        "fallback_priority": 2,
    },
    ModelBackend.ENSEMBLE.value: {
        "tier": "ensemble",
        "accuracy": 0.88,
        "latency_ms": 30.0,
        "cost": 25.0,
        "confidence_quality": 0.8,
        "reliability": 0.75,
        "fallback_priority": 1,
    },
    ModelBackend.EMBEDDING.value: {
        "tier": "embedding",
        "accuracy": 0.78,
        "latency_ms": 3.0,
        "cost": 3.0,
        "confidence_quality": 0.6,
        "reliability": 0.85,
        "fallback_priority": 3,
    },
}
