from __future__ import annotations

from ares.adaptive.profiles import ModelProfileRegistry

from .conftest import hermetic_profile_registry


def registry(cfg=None) -> ModelProfileRegistry:
    return hermetic_profile_registry(cfg)


class TestRegistryBasics:
    def test_default_registry_has_profiles(self):
        r = registry()
        assert len(r.available()) >= 3

    def test_get_by_name(self):
        r = registry()
        p = r.get("TF-IDF + Logistic Regression (Week 2)")
        assert p is not None
        assert p.computational_cost <= 1.0

    def test_get_by_internal_id(self):
        r = registry()
        assert r.get_by_internal_id("ce_quora").expected_accuracy >= 0.85

    def test_get_unknown_returns_none(self):
        assert registry().get("does-not-exist") is None

    def test_list_model_names(self):
        names = registry().list_model_names()
        assert "TF-IDF + Logistic Regression (Week 2)" in names


class TestConfigOverrides:
    def test_override_accuracy(self):
        cfg = {"model_profiles": {"week2_lr": {"expected_accuracy": 0.99}}}
        assert registry(cfg).get("TF-IDF + Logistic Regression (Week 2)").expected_accuracy == 0.99

    def test_override_latency_and_cost(self):
        cfg = {"model_profiles": {"ce_quora": {"expected_latency_ms": 100.0, "computational_cost": 50.0}}}
        p = registry(cfg).get("Cross-Encoder-Quora (Trained)")
        assert p.expected_latency_ms == 100.0
        assert p.computational_cost == 50.0


class TestSelection:
    def test_strongest_is_ensemble(self):
        assert registry().strongest().model_name == "Semantic Ensemble"

    def test_cheapest_is_classical_ml(self):
        assert registry().cheapest().model_name.startswith("TF-IDF")

    def test_compute_cost_unknown_defaults_to_one(self):
        assert registry().compute_cost("nope") == 1.0

    def test_profiles_have_full_metadata(self):
        p = registry().get("Cross-Encoder-Quora (Trained)")
        assert p.model_type == "cross-encoder"
        assert p.capability_tier == "cross-encoder"
        assert p.reliability > 0
        assert p.fallback_priority >= 0
