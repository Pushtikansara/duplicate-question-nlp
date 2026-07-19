from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestExplainabilityText:
    def test_generate_explanation_imports(self):
        from duplicate_question_app._explainability.text import generate_explanation
        assert callable(generate_explanation)

    def test_explanation_result_imports(self):
        from duplicate_question_app._explainability.text import ExplanationResult
        assert ExplanationResult is not None

    def test_generate_counterfactual_explanation_imports(self):
        from duplicate_question_app._explainability.text import generate_counterfactual_explanation
        assert callable(generate_counterfactual_explanation)

    def test_generate_feature_importance_imports(self):
        from duplicate_question_app._explainability.text import generate_feature_importance
        assert callable(generate_feature_importance)

    def test_explanation_result_fields(self):
        from duplicate_question_app._explainability.text import ExplanationResult, ExplanationLevel
        result = ExplanationResult(
            prediction="DUPLICATE", confidence=0.85, probability=0.85,
            level=ExplanationLevel.SIMPLE, summary="High similarity",
            reasons=["High word overlap"], details={"overlap": 0.7},
        )
        assert result.prediction == "DUPLICATE"
        assert result.confidence == 0.85


class TestExplainabilityTrace:
    def test_decision_trace_imports(self):
        from duplicate_question_app._explainability.trace import DecisionTrace, generate_decision_trace
        assert callable(generate_decision_trace)

    def test_decision_trace_dataclass(self):
        from duplicate_question_app._explainability.trace import DecisionTrace
        trace = DecisionTrace(
            question1_original="Q1", question2_original="Q2",
            question1_normalized="q1", question2_normalized="q2",
            top_tfidf_terms_q1=[("term", 0.5)], top_tfidf_terms_q2=[("term", 0.5)],
            abbreviations_list=[], synonyms_detected=[],
            named_entities_q1=[], named_entities_q2=[],
            adaptive_weights={}, models_agreeing=[], models_disagreeing=[],
        )
        assert trace.question1_original == "Q1"
        assert trace.final_prediction is not None


class TestExplainabilityAgreement:
    def test_agreement_dashboard_imports(self):
        from duplicate_question_app._explainability.agreement_dashboard import (
            AgreementDashboard, ModelLeaderboard,
            analyze_model_agreement, compute_model_leaderboard,
        )
        assert callable(analyze_model_agreement)

    def test_model_leaderboard_imports(self):
        from duplicate_question_app._explainability.agreement_dashboard import ModelLeaderboard
        lb = ModelLeaderboard(
            by_accuracy=[], by_confidence=[], by_calibration=[],
            by_agreement=[], by_influence=[], by_speed=[],
        )
        assert lb is not None

    def test_analyze_model_agreement_returns_result(self):
        from duplicate_question_app._explainability.agreement_dashboard import analyze_model_agreement
        with patch("duplicate_question_app._explainability.agreement_dashboard.get_agreement_report") as mock_agreement:
            mock_agreement.return_value = MagicMock()
            result = analyze_model_agreement("Q1", "A1")
            assert result is not None
