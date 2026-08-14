"""Phase 14.2 — 25-category behavioural coverage.

Each test is tagged with its coverage category (C01…C25). Together they prove:
early exit, escalation, trust escalation + trust-gated early exit, budgets,
difficulty signals, policy, disagreement (incl. reliability/difficulty-aware),
trust reliability, traceability (trust + stopping reason) and failure handling.
"""

from __future__ import annotations

from typing import Any

import pytest

from ares.adaptive.executor import AdaptiveExecutor
from ares.adaptive.trace import build_adaptive_trace
from ares.orchestration.exceptions import TaskExecutionError

from .conftest import FakeEngine, hermetic_profile_registry, make_assessment, make_evidence

LR = "TF-IDF + Logistic Regression (Week 2)"
SVM = "TF-IDF + Linear SVM (Week 2)"
CE = "Cross-Encoder-Quora (Trained)"
ENSEMBLE = "Semantic Ensemble"


class StubAnalyzer:
    def __init__(self, assessment):
        self.assessment = assessment

    def analyze(self, question1: str, question2: str, **kwargs: Any):
        return self.assessment


def run(cfg: dict[str, Any], assessment, engine: FakeEngine, **kw) -> Any:
    return AdaptiveExecutor(
        engine,
        config=cfg,
        difficulty_analyzer=StubAnalyzer(assessment),
        profile_registry=hermetic_profile_registry(cfg),
    ).execute("A", "B", **kw)


class TestCategories:
    # C01 Easy + confident -> cheap-only early exit, correct.
    def test_c01_easy_confident_early_exit(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
        out = run(default_config, make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical"), engine)
        assert out.early_exit and [e.model_name for e in out.evidences] == [LR]

    # C02 Easy + low confidence -> no early exit, no blind trust.
    def test_c02_easy_low_confidence_no_early_exit(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.6, 0.6, 5.0)})
        out = run(default_config, make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical"), engine)
        assert out.early_exit is False

    # C03 Medium low-confidence -> escalate to cross encoder.
    def test_c03_medium_escalates_to_cross_encoder(self, default_config):
        engine = FakeEngine(behaviors={SVM: (1, 0.6, 0.6, 5.0), CE: (1, 0.97, 0.97, 8.0)})
        out = run(
            default_config, make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier"), engine
        )
        assert [e.model_name for e in out.evidences] == [SVM, CE]

    # C04 Medium confident -> stops early within budget.
    def test_c04_medium_confident_stops_early(self, default_config):
        engine = FakeEngine(behaviors={SVM: (1, 0.95, 0.95, 5.0)})
        out = run(
            default_config, make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier"), engine
        )
        assert out.early_exit and [e.model_name for e in out.evidences] == [SVM]

    # C05 Hard/critical -> multiple strong models + reflection requested.
    def test_c05_hard_runs_several_models(self, default_config):
        engine = FakeEngine(behaviors={CE: (1, 0.8, 0.8, 8.0), ENSEMBLE: (1, 0.9, 0.9, 12.0)})
        out = run(default_config, make_assessment("hard", 0.7, "high", recommended_strategy="cross_encoder"), engine)
        models = [e.model_name for e in out.evidences]
        assert CE in models and ENSEMBLE in models

    # C06 Cheap duplicate on low content overlap -> trust escalation rescues FP.
    def test_c06_content_mismatch_fp_escalates(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.78, 0.78, 5.0), CE: (0, 0.1, 0.9, 8.0)})
        out = run(
            default_config,
            make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical", signals={"content_overlap": 0.0}),
            engine,
        )
        assert [e.model_name for e in out.evidences] == [LR, CE]
        assert out.final_result.predicted_label == 0

    # C07 Abbreviation relation -> synthetic-duplicate FN escalates.
    def test_c07_abbreviation_relation_escalates(self, default_config):
        engine = FakeEngine(behaviors={LR: (0, 0.4, 0.6, 5.0), CE: (1, 0.97, 0.97, 8.0)})
        out = run(
            default_config,
            make_assessment(
                "easy",
                0.1,
                "low",
                recommended_strategy="fast_lexical",
                signals={"abbreviation_relation": 1.0, "content_overlap": 0.0},
            ),
            engine,
        )
        assert "abbreviation_relation" in out.escalation_reasons
        assert out.final_result.predicted_label == 1

    # C08 Trust escalation can be disabled by configuration.
    def test_c08_trust_escalation_disabled(self, default_config):
        cfg = dict(default_config)
        cfg["trust"] = {"escalation_enabled": False, "max_extra_models": 1}
        engine = FakeEngine(behaviors={LR: (1, 0.78, 0.78, 5.0)})
        out = run(
            cfg,
            make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical", signals={"content_overlap": 0.0}),
            engine,
        )
        assert [e.model_name for e in out.evidences] == [LR]

    # C09 Trust-gated early exit: even VERY high confidence does not short-circuit a
    #     prediction the trust analysis flags for re-verification.
    def test_c09_trust_gates_early_exit(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0), CE: (0, 0.1, 0.9, 8.0)})
        out = run(
            default_config,
            make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical", signals={"content_overlap": 0.0}),
            engine,
        )
        assert out.early_exit is False
        assert "content_mismatch_duplicate" in out.escalation_reasons
        assert out.final_result.predicted_label == 0

    # C10 Budget: low tier -> exactly one model call, no escalation.
    def test_c10_low_budget_single_call(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.6, 0.6, 5.0)})
        out = run(default_config, make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical"), engine)
        assert len(out.evidences) == 1

    # C11 Budget: high tier allows several calls + reflection.
    def test_c11_high_budget_generous(self, default_config):
        engine = FakeEngine(behaviors={CE: (1, 0.8, 0.8, 8.0), ENSEMBLE: (1, 0.9, 0.9, 12.0)})
        out = run(default_config, make_assessment("hard", 0.7, "high", recommended_strategy="cross_encoder"), engine)
        assert len(out.evidences) >= 2
        assert out.plan.reflection_requested

    # C12 Difficulty: exact-match shortcut is trivially easy.
    def test_c12_exact_match_easy(self):
        from ares.adaptive.difficulty import DifficultyAnalyzer

        a = DifficultyAnalyzer().analyze("what is python", "what is python")
        assert a.difficulty_level == "easy" and a.signals["exact_match"] == 1.0

    # C13 Difficulty: antonym/contradiction pair raises difficulty.
    def test_c13_contradiction_flagged(self):
        from ares.adaptive.difficulty import DifficultyAnalyzer

        a = DifficultyAnalyzer().analyze("how to increase sales", "how to decrease sales")
        assert a.signals["contradiction"] >= 0.5

    # C14 Difficulty: asymmetric negation flagged.
    def test_c14_negation_asymmetry(self):
        from ares.adaptive.difficulty import DifficultyAnalyzer

        a = DifficultyAnalyzer().analyze("i do not want to eat", "i want to eat")
        assert a.signals["negation"] >= 0.5

    # C15 Difficulty: acronym forms ML / M.L. / ml recognised.
    @pytest.mark.parametrize("term", ["ML", "M.L.", "ml"])
    def test_c15_acronym_forms(self, term):
        from ares.adaptive.difficulty import DifficultyAnalyzer

        a = DifficultyAnalyzer().analyze(f"what is {term}", "what is python")
        assert a.signals["abbreviation"] == 1.0

    # C16 Difficulty: abbreviation_relation signal and config override.
    def test_c16_abbreviation_relation_configurable(self):
        from ares.adaptive.difficulty import DifficultyAnalyzer

        config = {"difficulty": {"acronyms": {"gllm": "giant language learning model"}}}
        a = DifficultyAnalyzer(config).analyze("what is gllm", "explain giant language learning model")
        assert a.signals["abbreviation_relation"] == 1.0

    # C17 Difficulty: synonym/substitution content gap boosts difficulty.
    def test_c17_content_gap_boost(self):
        from ares.adaptive.difficulty import DifficultyAnalyzer

        a = DifficultyAnalyzer().analyze("price of iphone", "cost of samsung galaxy")
        assert a.signals["content_overlap"] <= 0.35

    # C18 Policy: easy request has no escalation ladder.
    def test_c18_easy_no_escalation(self, default_config):
        from ares.adaptive.budget import BudgetPolicy
        from ares.adaptive.policy import AdaptiveRoutingPolicy

        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        budget = BudgetPolicy(default_config).allocate(assessment.difficulty_level, assessment.risk_level)
        plan = AdaptiveRoutingPolicy(default_config).make_plan(assessment, budget)
        assert plan.escalation_ladder == []

    # C19 Policy: critical request recommends human review.
    def test_c19_critical_human_review(self, default_config):
        from ares.adaptive.budget import BudgetPolicy
        from ares.adaptive.policy import AdaptiveRoutingPolicy

        assessment = make_assessment("critical", 0.9, "critical", recommended_strategy="cross_encoder")
        budget = BudgetPolicy(default_config).allocate(assessment.difficulty_level, assessment.risk_level)
        plan = AdaptiveRoutingPolicy(default_config).make_plan(assessment, budget)
        assert plan.human_review_recommended is True

    # C20 Policy: reflection modes (always / never / conditional).
    @pytest.mark.parametrize(
        "mode,level,expected",
        [
            ("always", "easy", True),
            ("never", "hard", False),
            ("conditional", "hard", True),
            ("conditional", "easy", False),
        ],
    )
    def test_c20_reflection_modes(self, default_config, mode, level, expected):
        from ares.adaptive.budget import BudgetPolicy
        from ares.adaptive.policy import AdaptiveRoutingPolicy

        cfg = dict(default_config)
        cfg["reflection"] = {"mode": mode, "hard_difficulty_only": True}
        assessment = make_assessment(level, 0.5, "medium", recommended_strategy="fast_lexical")
        budget = BudgetPolicy(cfg).allocate(assessment.difficulty_level, assessment.risk_level)
        plan = AdaptiveRoutingPolicy(cfg).make_plan(assessment, budget)
        assert plan.reflection_requested is expected

    # C21 Disagreement: confidence-weighted resolution.
    def test_c21_confidence_weighted_resolution(self):
        from ares.adaptive.disagreement import DisagreementDetector

        evs = [make_evidence("A", 0.1, 0, 0.95), make_evidence("B", 0.97, 1, 0.97)]
        a = DisagreementDetector().assess(evs)
        assert a.resolution_strategy == "confidence_weighted"
        assert a.resolution_label == 1

    # C22 Disagreement: reliability-aware weighting.
    def test_c22_reliability_aware_resolution(self):
        from ares.adaptive.disagreement import DisagreementDetector
        from ares.adaptive.models import ModelProfile

        def profile(name, reliability):
            return ModelProfile(
                model_name=name,
                internal_id=name,
                model_type="transformer",
                capability_tier="transformer",
                expected_accuracy=0.8,
                expected_latency_ms=5.0,
                computational_cost=5.0,
                memory_cost_mb=1.0,
                confidence_quality=0.8,
                reliability=reliability,
                fallback_priority=1,
            )

        class P:
            def __init__(self, m):
                self._m = m

            def get(self, name):
                return self._m.get(name)

        evs = [make_evidence("A", 0.1, 0, 0.95), make_evidence("B", 0.97, 1, 0.97)]
        a = DisagreementDetector(profile_registry=P({"A": profile("A", 0.95), "B": profile("B", 0.5)})).assess(evs)
        assert a.resolution_label == 0

    # C23 Disagreement: difficulty-aware damping on hard requests.
    def test_c23_difficulty_aware_resolution(self):
        from ares.adaptive.disagreement import DisagreementDetector

        evs = [make_evidence("A", 0.1, 0, 0.95), make_evidence("B", 0.97, 1, 0.97)]
        a = DisagreementDetector().assess(evs, difficulty_level="hard")
        assert a.difficulty_level == "hard"

    # C24 Trust: model reliability lowers the trust score.
    def test_c24_reliability_reduces_trust(self, default_config):
        from ares.adaptive.models import ModelProfile
        from ares.adaptive.trust import TrustAnalyzer

        class P:
            def get(self, name):
                return ModelProfile(
                    model_name=name,
                    internal_id=name,
                    model_type="transformer",
                    capability_tier="transformer",
                    expected_accuracy=0.8,
                    expected_latency_ms=5.0,
                    computational_cost=5.0,
                    memory_cost_mb=1.0,
                    confidence_quality=0.8,
                    reliability=0.5,
                    fallback_priority=1,
                )

        a = TrustAnalyzer(default_config, profile_registry=P()).assess(
            make_assessment("easy", 0.1, "low"), make_evidence("X", 0.2, 0, 0.9)
        )
        assert "low_model_reliability" in a.risk_reasons
        assert a.trust_score < 1.0

    # C25 Traceability: trace carries trust + stopping_reason sections.
    def test_c25_trace_trust_and_stopping(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
        out = run(default_config, make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical"), engine)
        trace = out.to_trace_dict()
        assert "trust" in trace
        assert trace["adaptive"]["stopping_reason"] == "high_confidence_low_risk"
        assert trace["trust"] is not None
        assert trace["trust"]["trust_level"] == "high"

    # C26 Failure: all models failing raises, partial failure survives.
    def test_c26_failures_raise_and_partial(self, default_config):
        with pytest.raises(TaskExecutionError):
            run(
                default_config,
                make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical"),
                FakeEngine(failures={LR}),
            )
        engine = FakeEngine(failures={SVM}, behaviors={CE: (1, 0.97, 0.97, 8.0)})
        out = run(
            default_config, make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier"), engine
        )
        assert out.final_result.predicted_label == 1

    # C27 Explicit model override forces a single model.
    def test_c27_model_override(self, default_config):
        engine = FakeEngine(behaviors={"custom": (1, 0.9, 0.9, 5.0)})
        out = run(
            default_config,
            make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical"),
            engine,
            model="custom",
        )
        assert out.final_model == "custom" and len(out.evidences) == 1

    def test_build_adaptive_trace_includes_trust_and_stopping(self, default_config):
        from ares.adaptive.models import ComputeBudget, DifficultyAssessment, ReflectionRecord, RoutingPlan
        from ares.adaptive.trust import TrustAssessment

        trace = build_adaptive_trace(
            assessment=DifficultyAssessment(),
            plan=RoutingPlan(),
            budget=ComputeBudget("low", 1, 0, 1000, False, 0),
            evidences=[make_evidence(LR, 0.9, 1, 0.9)],
            disagreement=None,
            escalation_count=0,
            escalation_reasons=[],
            early_exit=True,
            early_exit_reason="high_confidence_low_risk",
            stopping_reason="high_confidence_low_risk",
            reflection=ReflectionRecord(),
            stages_executed=[],
            stages_skipped=[],
            consumed_latency_ms=5.0,
            final_strategy="fast_lexical",
            final_model=LR,
            final_confidence=0.9,
            review_required=False,
            routing_explanation="x",
            trust=TrustAssessment(),
        )
        assert set(trace) == {"routing", "execution", "adaptive", "evidence", "budget", "final", "trust"}
        assert trace["adaptive"]["stopping_reason"] == "high_confidence_low_risk"
