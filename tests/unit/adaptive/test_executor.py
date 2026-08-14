from __future__ import annotations

from typing import Any

import pytest

from ares.adaptive.executor import AdaptiveExecutor
from ares.orchestration.exceptions import TaskExecutionError

from .conftest import FakeEngine, make_assessment

LR = "TF-IDF + Logistic Regression (Week 2)"
SVM = "TF-IDF + Linear SVM (Week 2)"
CE = "Cross-Encoder-Quora (Trained)"
ENSEMBLE = "Semantic Ensemble"


class StubAnalyzer:
    def __init__(self, assessment):
        self.assessment = assessment

    def analyze(self, question1: str, question2: str, **kwargs: Any):
        return self.assessment


def build_executor(cfg: dict[str, Any], assessment, engine: FakeEngine) -> AdaptiveExecutor:
    return AdaptiveExecutor(
        engine,
        config=cfg,
        difficulty_analyzer=StubAnalyzer(assessment),
    )


class TestEasyEarlyExit:
    def test_confident_easy_exits_after_single_model(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.early_exit is True
        assert run.early_exit_reason == "high_confidence_low_risk"
        assert [e.model_name for e in run.evidences] == [LR]
        assert run.final_model == LR
        assert run.final_strategy == "fast_lexical"
        assert run.final_result.predicted_label == 1

    def test_low_confidence_easy_does_not_early_exit(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.6, 0.6, 5.0)})
        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.early_exit is False
        assert run.final_result.predicted_label == 1


class TestEscalation:
    def test_medium_with_low_confidence_escalates_to_cross_encoder(self, default_config):
        engine = FakeEngine(behaviors={SVM: (1, 0.6, 0.6, 5.0), CE: (1, 0.97, 0.97, 8.0)})
        assessment = make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.early_exit is False
        assert [e.model_name for e in run.evidences] == [SVM, CE]
        assert run.escalation_count == 1
        assert run.final_model == CE

    def test_medium_confident_stops_early(self, default_config):
        engine = FakeEngine(behaviors={SVM: (1, 0.95, 0.95, 5.0)})
        assessment = make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.early_exit is True
        assert [e.model_name for e in run.evidences] == [SVM]

    def test_hard_runs_cross_encoder_and_ensemble(self, default_config):
        engine = FakeEngine(behaviors={CE: (1, 0.8, 0.8, 8.0), ENSEMBLE: (1, 0.9, 0.9, 12.0)})
        assessment = make_assessment("hard", 0.7, "high", recommended_strategy="cross_encoder")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        models = [e.model_name for e in run.evidences]
        assert CE in models and ENSEMBLE in models
        assert run.escalation_count >= 1


class TestTrustEscalation:
    def test_cheap_duplicate_on_content_mismatch_escalates(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.78, 0.78, 5.0), CE: (0, 0.1, 0.9, 8.0)})
        assessment = make_assessment(
            "easy", 0.1, "low", recommended_strategy="fast_lexical", signals={"content_overlap": 0.0}
        )
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.early_exit is False
        assert [e.model_name for e in run.evidences] == [LR, CE]
        assert "content_mismatch_duplicate" in run.escalation_reasons
        assert run.final_result.predicted_label == 0

    def test_cheap_non_duplicate_on_content_mismatch_does_not_escalate(self, default_config):
        engine = FakeEngine(behaviors={LR: (0, 0.3, 0.7, 5.0), CE: (0, 0.1, 0.9, 8.0)})
        assessment = make_assessment(
            "easy", 0.1, "low", recommended_strategy="fast_lexical", signals={"content_overlap": 0.0}
        )
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert [e.model_name for e in run.evidences] == [LR]
        assert run.final_result.predicted_label == 0

    def test_abbreviation_relation_escalates_to_cross_encoder(self, default_config):
        engine = FakeEngine(behaviors={LR: (0, 0.4, 0.6, 5.0), CE: (1, 0.97, 0.97, 8.0)})
        assessment = make_assessment(
            "easy",
            0.1,
            "low",
            recommended_strategy="fast_lexical",
            signals={"content_overlap": 0.0, "abbreviation_relation": 1.0},
        )
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert [e.model_name for e in run.evidences] == [LR, CE]
        assert "abbreviation_relation" in run.escalation_reasons
        assert run.final_result.predicted_label == 1

    def test_trust_escalation_can_be_disabled(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.78, 0.78, 5.0), CE: (1, 0.97, 0.97, 8.0)})
        assessment = make_assessment(
            "easy", 0.1, "low", recommended_strategy="fast_lexical", signals={"content_overlap": 0.0}
        )
        cfg = dict(default_config)
        cfg["trust"] = {"escalation_enabled": False, "max_extra_models": 1}
        run = build_executor(cfg, assessment, engine).execute("A", "B")

        assert [e.model_name for e in run.evidences] == [LR]


class TestModelFailures:
    def test_single_model_failed_raises(self, default_config):
        engine = FakeEngine(failures={LR})
        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        with pytest.raises(TaskExecutionError):
            build_executor(default_config, assessment, engine).execute("A", "B")

    def test_all_models_failed_raises(self, default_config):
        engine = FakeEngine(failures={SVM, CE})
        assessment = make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier")
        with pytest.raises(TaskExecutionError):
            build_executor(default_config, assessment, engine).execute("A", "B")

    def test_partial_failure_still_returns_result(self, default_config):
        engine = FakeEngine(failures={SVM}, behaviors={CE: (1, 0.97, 0.97, 8.0)})
        assessment = make_assessment("medium", 0.5, "medium", recommended_strategy="baseline_classifier")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.evidences[0].error is not None
        assert run.final_result.predicted_label == 1
        assert run.final_model == CE


class TestModelOverride:
    def test_explicit_model_override_runs_only_that_model(self, default_config):
        engine = FakeEngine(behaviors={"my-custom-model": (1, 0.9, 0.9, 5.0)})
        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        run = build_executor(default_config, assessment, engine).execute("A", "B", model="my-custom-model")

        assert run.plan.initial_model == "my-custom-model"
        assert run.final_model == "my-custom-model"


class TestRunMetadata:
    def test_metadata_populated(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        run = build_executor(default_config, assessment, engine).execute("A", "B")

        assert run.assessment is not None
        assert run.plan is not None
        assert run.budget is not None
        assert run.total_latency_ms >= 0.0
        assert run.final_confidence >= 0.0
        assert run.final_result is not None

    def test_last_run_stored_on_executor(self, default_config):
        engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
        assessment = make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")
        ex = build_executor(default_config, assessment, engine)
        ex.execute("A", "B")
        assert ex.last_run is not None
        assert ex.last_run.plan.initial_strategy == "fast_lexical"
