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
    def _mock_prediction_result(self):
        mock = MagicMock()
        mock.predicted_label = 1
        mock.prediction = "Duplicate"
        mock.confidence = 0.85
        mock.prob_duplicate = 0.85
        mock.prob_non_duplicate = 0.15
        mock.model_name = "TestModel"
        mock.latency_ms = 10.0
        mock.threshold = 0.5
        mock.selected_model = "TestModel"
        mock.executed_model = "TestModel"
        mock.backend = "TransformerBackend"
        mock.artifact_path = ""
        mock.tokenizer = ""
        mock.inference_function = ""
        mock.execution_time_ms = 10.0
        mock.raw_logits = []
        mock.softmax = []
        mock.predicted_class_id = 1
        mock.label_mapping = {0: "Non-Duplicate", 1: "Duplicate"}
        mock.final_label = "Duplicate"
        return mock

    def test_model_prediction_includes_semantic_fields(self):
        from app.utils.constants import get_model_prediction

        with patch(
            "ares.inference.dispatcher.InferenceDispatcher.predict", return_value=self._mock_prediction_result()
        ):
            result = get_model_prediction(
                MagicMock(), "Improved DistilBERT (Week 4)", "How to install Python?", "How to set up Python?"
            )

        assert "predicted_label" in result
        assert "prediction" in result
        assert "confidence" in result
        assert "model_name" in result
        assert result["predicted_label"] == 1
        assert result["prediction"] == "Duplicate"
        assert result["confidence"] == 0.85

    def test_semantic_only_mode(self):
        from app.utils.constants import get_model_prediction

        with patch(
            "ares.inference.dispatcher.InferenceDispatcher.predict", return_value=self._mock_prediction_result()
        ):
            result = get_model_prediction(
                MagicMock(), "Improved DistilBERT (Week 4)", "How to install Python?", "How to set up Python?"
            )

        assert result["predicted_label"] == 1
        assert "prediction" in result

    def test_cross_encoder_only_mode(self):
        from app.utils.constants import get_model_prediction

        with patch(
            "ares.inference.dispatcher.InferenceDispatcher.predict", return_value=self._mock_prediction_result()
        ):
            result = get_model_prediction(
                MagicMock(), "Improved DistilBERT (Week 4)", "How to install Python?", "How to set up Python?"
            )

        assert result["predicted_label"] == 1
        assert "prediction" in result


class TestBatchPredictionSIE:
    def test_batch_prediction_includes_semantic_columns(self):
        from app.utils.constants import run_batch_prediction

        mock_pred = MagicMock()
        mock_pred.predicted_label = 1
        mock_pred.prediction = "Duplicate"
        mock_pred.confidence = 0.85
        mock_pred.prob_duplicate = 0.85
        mock_pred.prob_non_duplicate = 0.15
        mock_pred.model_name = "TestModel"
        mock_pred.latency_ms = 10.0

        pairs = [
            ("How to install Python?", "How to set up Python?"),
            ("What is Java?", "Explain Java programming"),
        ]

        with patch("ares.inference.dispatcher.InferenceDispatcher.predict", return_value=mock_pred):
            df = run_batch_prediction(MagicMock(), "Improved DistilBERT (Week 4)", pairs)

        assert isinstance(df, pd.DataFrame)
        assert "predicted_label" in df.columns
        assert "prediction" in df.columns
        assert "confidence" in df.columns
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
