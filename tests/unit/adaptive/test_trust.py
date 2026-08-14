from __future__ import annotations

from typing import Any

from ares.adaptive.config_loader import load_adaptive_config
from ares.adaptive.models import ModelProfile
from ares.adaptive.trust import DEFAULT_ESCALATION_REASONS, TrustAnalyzer

from .conftest import make_assessment, make_evidence

LR = "TF-IDF + Logistic Regression (Week 2)"
CE = "Cross-Encoder-Quora (Trained)"


class StubProfiles:
    def __init__(self, profiles: dict[str, ModelProfile] | None = None) -> None:
        self._profiles = profiles or {}

    def resolve(self, name: str) -> None:
        pass

    def get(self, model_name: str) -> ModelProfile | None:
        return self._profiles.get(model_name)


def make_profile(model_name: str, reliability: float, confidence_quality: float = 0.8) -> ModelProfile:
    return ModelProfile(
        model_name=model_name,
        internal_id="stub",
        model_type="transformer",
        capability_tier="transformer",
        expected_accuracy=0.9,
        expected_latency_ms=5.0,
        computational_cost=5.0,
        memory_cost_mb=1.0,
        confidence_quality=confidence_quality,
        reliability=reliability,
        fallback_priority=1,
    )


def build_analyzer(profiles: dict[str, ModelProfile] | None = None, config: dict[str, Any] | None = None):
    return TrustAnalyzer(config or load_adaptive_config(), profile_registry=StubProfiles(profiles))


class TestTrustBase:
    def test_trusted_prediction_scores_high(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        assessment = make_assessment("easy", 0.1, "low", signals={"content_overlap": 0.8})
        evidence = make_evidence(LR, 0.2, 0, 0.9)
        trust = analyzer.assess(assessment, evidence)

        assert trust.trust_level == "high"
        assert trust.escalation_required is False
        assert trust.risk_reasons == []

    def test_trust_level_threshold_boundary(self):
        analyzer = build_analyzer()
        low = analyzer.assess(make_assessment("easy", 0.1, "low"), None)
        assert low.trust_score == 1.0
        assert low.trust_level == "high"

    def test_todict_surface(self):
        analyzer = build_analyzer()
        trust = analyzer.assess(make_assessment("easy", 0.1, "low"), None)
        data = trust.to_dict()
        for key in (
            "trust_score",
            "trust_level",
            "escalation_required",
            "escalation_reasons",
            "risk_reasons",
            "reliability",
            "evidence_model",
            "explanation",
        ):
            assert key in data


class TestAbbreviationRelation:
    def test_relation_escalates(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        assessment = make_assessment("easy", 0.1, "low", signals={"abbreviation_relation": 1.0, "content_overlap": 0.0})
        evidence = make_evidence(LR, 0.3, 0, 0.6)
        trust = analyzer.assess(assessment, evidence)

        assert trust.escalation_required is True
        assert "abbreviation_relation" in trust.escalation_reasons
        assert trust.trust_score < 1.0

    def test_below_threshold_does_not_escalate(self, default_config):
        cfg = dict(default_config)
        cfg["trust"] = {
            **cfg.get("trust", {}),
            "abbreviation_relation_min": 0.9,
        }
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)}, config=cfg)
        assessment = make_assessment("easy", 0.1, "low", signals={"abbreviation_relation": 0.5})
        trust = analyzer.assess(assessment, make_evidence(LR, 0.3, 0, 0.6))

        assert trust.escalation_required is False


class TestContentMismatch:
    def test_duplicate_on_low_overlap_escalates(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        assessment = make_assessment("easy", 0.1, "low", signals={"content_overlap": 0.0})
        trust = analyzer.assess(assessment, make_evidence(LR, 0.78, 1, 0.78))

        assert trust.escalation_required is True
        assert "content_mismatch_duplicate" in trust.escalation_reasons

    def test_duplicate_on_high_overlap_does_not_escalate(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        assessment = make_assessment("easy", 0.1, "low", signals={"content_overlap": 0.8})
        trust = analyzer.assess(assessment, make_evidence(LR, 0.78, 1, 0.78))

        assert trust.escalation_required is False
        assert "content_mismatch_duplicate" not in trust.risk_reasons

    def test_non_duplicate_on_low_overlap_does_not_escalate(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        assessment = make_assessment("easy", 0.1, "low", signals={"content_overlap": 0.0})
        trust = analyzer.assess(assessment, make_evidence(LR, 0.3, 0, 0.7))

        assert trust.escalation_required is False

    def test_missing_overlap_signal_is_not_mismatch(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        assessment = make_assessment("easy", 0.1, "low")
        trust = analyzer.assess(assessment, make_evidence(LR, 0.78, 1, 0.78))

        assert trust.escalation_required is False


class TestReliability:
    def test_unreliable_model_reduces_trust(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.5)})
        trust = analyzer.assess(make_assessment("easy", 0.1, "low"), make_evidence(LR, 0.2, 0, 0.9))

        assert "low_model_reliability" in trust.risk_reasons
        assert trust.reliability == 0.5
        assert trust.trust_score < 1.0
        assert trust.trust_level == "medium"

    def test_reliable_model_no_reliability_penalty(self):
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)})
        trust = analyzer.assess(make_assessment("easy", 0.1, "low"), make_evidence(LR, 0.2, 0, 0.9))

        assert "low_model_reliability" not in trust.risk_reasons


class TestConfig:
    def test_escalation_reasons_tunable(self, default_config):
        cfg = dict(default_config)
        cfg["trust"] = {**cfg.get("trust", {}), "escalation_reasons": ["abbreviation_relation"]}
        analyzer = build_analyzer({LR: make_profile(LR, 0.9)}, config=cfg)
        assessment = make_assessment("easy", 0.1, "low", signals={"abbreviation_relation": 1.0, "content_overlap": 0.0})
        trust = analyzer.assess(assessment, make_evidence(LR, 0.78, 1, 0.78))

        assert trust.escalation_required is True
        assert trust.escalation_reasons == ["abbreviation_relation"]
        assert "content_mismatch_duplicate" not in trust.escalation_reasons

    def test_default_escalation_reasons_constant(self):
        assert {"abbreviation_relation", "content_mismatch_duplicate"} == DEFAULT_ESCALATION_REASONS
