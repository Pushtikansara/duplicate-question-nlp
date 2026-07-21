from __future__ import annotations

from duplicate_question_app._integration.pipeline_context import PipelineContext
from duplicate_question_app._integration.validation import (
    validate_pipeline_context,
    validate_prediction_unchanged,
)


class TestValidation:
    def test_validate_valid_context(self):
        ctx = PipelineContext(question_a="q1", question_b="q2")
        result = validate_pipeline_context(ctx)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_none_context(self):
        result = validate_pipeline_context(None)
        assert result.valid is False
        assert "None" in result.errors[0]

    def test_validate_missing_question(self):
        ctx = PipelineContext(question_a="", question_b="q2")
        result = validate_pipeline_context(ctx)
        assert result.valid is False

    def test_predictions_unchanged(self):
        before = {"predicted_label": 1, "prediction": "Duplicate", "prob_duplicate": 0.95, "prob_non_duplicate": 0.05}
        after = {"predicted_label": 1, "prediction": "Duplicate", "prob_duplicate": 0.95, "prob_non_duplicate": 0.05}
        result = validate_prediction_unchanged(before, after)
        assert result.valid is True

    def test_predictions_changed(self):
        before = {"predicted_label": 1, "prediction": "Duplicate", "prob_duplicate": 0.95, "prob_non_duplicate": 0.05}
        after = {
            "predicted_label": 0,
            "prediction": "Non-Duplicate",
            "prob_duplicate": 0.30,
            "prob_non_duplicate": 0.70,
        }
        result = validate_prediction_unchanged(before, after)
        assert result.valid is False
        assert len(result.errors) > 0
