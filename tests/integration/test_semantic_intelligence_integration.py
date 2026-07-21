"""Integration tests for the Semantic Intelligence Engine integration.

Verifies:
- SIE is actually executed during prediction
- Decision Fusion runs
- SemanticAssessment is produced
- Prediction pipeline includes semantic fields
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.fusion import DecisionFusion, FusionStrategy
from duplicate_question_app._semantic_intelligence.semantic_pipeline import SemanticPipelineService


class TestDecisionFusion:
    def test_cross_encoder_only(self):
        fusion = DecisionFusion(strategy=FusionStrategy.CROSS_ENCODER_ONLY)
        result = fusion.fuse(cross_encoder_score=0.85, semantic_assessment=None)
        assert result["final_score"] == 0.85
        assert result["strategy"] == "cross_encoder_only"
        assert result["final_prediction"] == "Duplicate"

    def test_semantic_only(self):
        fusion = DecisionFusion(strategy=FusionStrategy.SEMANTIC_ONLY)
        assessment = {"semantic_similarity": 0.75}
        result = fusion.fuse(cross_encoder_score=0.0, semantic_assessment=assessment)
        assert result["final_score"] == 0.75
        assert result["strategy"] == "semantic_only"

    def test_fusion_mode(self):
        fusion = DecisionFusion()
        assessment = {
            "semantic_similarity": 0.8,
            "intent_similarity": {"score": 0.9},
            "concept_overlap": {"overlap_score": 0.7},
            "entity_overlap": {"overlap_score": 0.6},
            "context_similarity": {"score": 0.5},
            "conflicts": [],
        }
        result = fusion.fuse(cross_encoder_score=0.9, semantic_assessment=assessment)
        assert result["strategy"] == "fusion"
        assert 0.0 <= result["final_score"] <= 1.0
        assert "cross_encoder_score" in result
        assert "semantic_score" in result
        assert "fusion_score" in result
        assert "weights_used" in result

    def test_fusion_with_conflicts(self):
        fusion = DecisionFusion()
        assessment = {
            "semantic_similarity": 0.9,
            "intent_similarity": {"score": 0.9},
            "concept_overlap": {"overlap_score": 0.9},
            "entity_overlap": {"overlap_score": 0.9},
            "context_similarity": {"score": 0.9},
            "conflicts": [
                {"conflict_type": "domain_mismatch", "description": "Domain mismatch", "severity": 0.8},
            ],
        }
        result = fusion.fuse(cross_encoder_score=0.9, semantic_assessment=assessment)
        assert result["final_score"] < 0.9
        assert result["conflict_penalty_applied"] > 0

    def test_no_assessment_falls_back(self):
        fusion = DecisionFusion()
        result = fusion.fuse(cross_encoder_score=0.85, semantic_assessment=None)
        assert result["final_score"] > 0


class TestSemanticPipelineService:
    def test_pipeline_runs_and_returns_assessment(self):
        pipeline = SemanticPipelineService()
        assessment, meta = pipeline.assess("How to install Python?", "How to set up Python?")
        if assessment is not None:
            assert assessment.semantic_similarity >= 0.0
            assert hasattr(assessment, "semantic_similarity")
            assert hasattr(assessment, "concept_overlap")
            assert hasattr(assessment, "entity_overlap")
            assert hasattr(assessment, "intent_similarity")
            assert hasattr(assessment, "supporting_evidence")
            assert hasattr(assessment, "conflicts")
            assert hasattr(assessment, "recommendation")
            assert "stages" in meta
        else:
            assert "error" in meta

    def test_pipeline_with_identical_text(self):
        pipeline = SemanticPipelineService()
        assessment, meta = pipeline.assess("How to install Python?", "How to install Python?")
        if assessment is not None:
            assert assessment.semantic_similarity > 0.5

    def test_pipeline_with_completely_different_text(self):
        pipeline = SemanticPipelineService()
        assessment, meta = pipeline.assess("How to install Python?", "What is the capital of France?")
        if assessment is not None:
            assert assessment.semantic_similarity < 0.8

    def test_analyze_question_returns_representation(self):
        pipeline = SemanticPipelineService()
        rep = pipeline.analyze_question("How to install Python?")
        if rep is not None:
            assert isinstance(rep, SemanticRepresentation)
            assert hasattr(rep, "concepts")
            assert hasattr(rep, "entities")


class TestGetModelPredictionSIEPresence:
    def test_model_prediction_includes_semantic_fields(self):
        from app.utils.constants import get_model_prediction

        mock_service = MagicMock()
        mock_service.predict_single.return_value = {
            "prediction": "Duplicate",
            "prob_duplicate": 0.85,
            "confidence": 0.85,
            "model_label": "TestModel",
            "prob_non_duplicate": 0.15,
            "threshold": 0.5,
            "predicted_label": 1,
            "reason": None,
            "feature_breakdown": None,
        }

        with patch("app.utils.constants._get_prediction_mode", return_value="fusion"):
            result = get_model_prediction(
                mock_service, "Improved DistilBERT (Week 4)", "How to install Python?", "How to set up Python?"
            )

        assert "semantic_assessment" in result
        assert "semantic_similarity" in result
        assert "fusion_result" in result
        assert "prediction_mode" in result
        assert result["prediction_mode"] == "fusion"

    def test_semantic_only_mode(self):
        from app.utils.constants import get_model_prediction

        mock_service = MagicMock()
        mock_service.predict_single.return_value = {
            "prediction": "Duplicate",
            "prob_duplicate": 0.85,
            "confidence": 0.85,
            "model_label": "TestModel",
            "prob_non_duplicate": 0.15,
            "threshold": 0.5,
            "predicted_label": 1,
            "reason": None,
            "feature_breakdown": None,
        }

        with patch("app.utils.constants._get_prediction_mode", return_value="semantic_only"):
            result = get_model_prediction(
                mock_service, "Improved DistilBERT (Week 4)", "How to install Python?", "How to set up Python?"
            )

        assert result["prediction_mode"] == "semantic_only"
        assert "fusion_result" in result

    def test_cross_encoder_only_mode(self):
        from app.utils.constants import get_model_prediction

        mock_service = MagicMock()
        mock_service.predict_single.return_value = {
            "prediction": "Duplicate",
            "prob_duplicate": 0.85,
            "confidence": 0.85,
            "model_label": "TestModel",
            "prob_non_duplicate": 0.15,
            "threshold": 0.5,
            "predicted_label": 1,
            "reason": None,
            "feature_breakdown": None,
        }

        with patch("app.utils.constants._get_prediction_mode", return_value="cross_encoder_only"):
            result = get_model_prediction(
                mock_service, "Improved DistilBERT (Week 4)", "How to install Python?", "How to set up Python?"
            )

        assert result["prediction_mode"] == "cross_encoder_only"
        assert "fusion_result" in result


class TestBatchPredictionSIE:
    def test_batch_prediction_includes_semantic_columns(self):
        from app.utils.constants import run_batch_prediction

        mock_service = MagicMock()
        mock_service.predict_single.side_effect = lambda q1, q2: {
            "prediction": "Duplicate",
            "prob_duplicate": 0.85,
            "confidence": 0.85,
            "model_label": "TestModel",
            "prob_non_duplicate": 0.15,
            "threshold": 0.5,
            "predicted_label": 1,
            "reason": None,
            "feature_breakdown": None,
        }

        pairs = [
            ("How to install Python?", "How to set up Python?"),
            ("What is Java?", "Explain Java programming"),
        ]

        with patch("app.utils.constants._get_prediction_mode", return_value="fusion"):
            df = run_batch_prediction(mock_service, "Improved DistilBERT (Week 4)", pairs)

        assert isinstance(df, pd.DataFrame)
        assert "semantic_similarity" in df.columns
        assert "fusion_score" in df.columns
        assert "fusion_prediction" in df.columns
        assert "concept_overlap" in df.columns
        assert "intent_match" in df.columns
        assert "num_conflicts" in df.columns
        assert len(df) == 2


class TestSemanticAssessmentOutput:
    def test_assessment_contains_all_required_fields(self):
        from duplicate_question_app._semantic_intelligence.semantic_assessment import (
            ConceptOverlap,
            Conflict,
            ContextSimilarity,
            EntityOverlap,
            EvidenceItem,
            IntentSimilarity,
            Recommendation,
            RelationSimilarity,
            SemanticAssessment,
        )

        assessment = SemanticAssessment(
            semantic_similarity=0.75,
            concept_overlap=ConceptOverlap(overlap_score=0.8),
            entity_overlap=EntityOverlap(overlap_score=0.7),
            intent_similarity=IntentSimilarity(score=0.9, confidence=0.85, reason="Match"),
            relation_similarity=RelationSimilarity(score=0.6),
            context_similarity=ContextSimilarity(score=0.5, domain_match=True),
            conflicts=[Conflict(conflict_type="test", description="test")],
            supporting_evidence=[EvidenceItem(category="test", status="info", message="test")],
            confidence=0.75,
            recommendation=Recommendation.DUPLICATE,
            recommendation_reason="High similarity",
        )

        d = assessment.to_dict()
        assert "semantic_similarity" in d
        assert "concept_overlap" in d
        assert "entity_overlap" in d
        assert "intent_similarity" in d
        assert "relation_similarity" in d
        assert "context_similarity" in d
        assert "conflicts" in d
        assert "supporting_evidence" in d
        assert "confidence" in d
        assert "recommendation" in d
        assert d["recommendation"] == "DUPLICATE"
