from __future__ import annotations

import numpy as np
import pytest


class TestEvaluationMetrics:
    def test_evaluation_metrics_creation(self):
        from duplicate_question_app._evaluation.metrics import EvaluationMetrics
        metrics = EvaluationMetrics(
            accuracy=0.85, precision=0.83, recall=0.87, f1=0.85, roc_auc=0.92,
            pr_auc=0.90, brier_score=0.12, log_loss=0.35, ece=0.05, mce=0.10,
            confusion_matrix=np.array([[10, 2], [3, 15]]),
            classification_report="report",
        )
        assert metrics.accuracy == 0.85
        assert metrics.f1 == 0.85

    def test_generate_evaluation_report_imports(self):
        from duplicate_question_app._evaluation.metrics import generate_evaluation_report
        assert callable(generate_evaluation_report)

    def test_compare_models_import(self):
        from duplicate_question_app._evaluation.metrics import compare_models
        assert callable(compare_models)

    def test_evaluate_model_import(self):
        from duplicate_question_app._evaluation.metrics import evaluate_model
        assert callable(evaluate_model)


class TestErrorAnalysis:
    def test_error_category_fields(self):
        from duplicate_question_app._evaluation.error_analysis import ErrorCategory
        from dataclasses import fields
        field_names = {f.name for f in fields(ErrorCategory)}
        assert "name" in field_names
        assert "description" in field_names
        assert "detected" in field_names

    def test_categorize_error_true_positive(self):
        from duplicate_question_app._evaluation.error_analysis import categorize_error
        cat = categorize_error("Q1", "Q2", predicted_label=1, true_label=1, prob_duplicate=0.8)
        assert isinstance(cat, list)

    def test_categorize_error_false_positive(self):
        from duplicate_question_app._evaluation.error_analysis import categorize_error
        cat = categorize_error("Q1", "Q2", predicted_label=1, true_label=0, prob_duplicate=0.8)
        assert isinstance(cat, list)

    def test_categorize_error_false_negative(self):
        from duplicate_question_app._evaluation.error_analysis import categorize_error
        cat = categorize_error("Q1", "Q2", predicted_label=0, true_label=1, prob_duplicate=0.3)
        assert isinstance(cat, list)

    def test_classify_hardness_imports(self):
        from duplicate_question_app._evaluation.error_analysis import classify_hardness
        assert callable(classify_hardness)

    def test_mine_hard_examples_imports(self):
        from duplicate_question_app._evaluation.error_analysis import mine_hard_examples
        assert callable(mine_hard_examples)

    def test_classify_hardness_returns_result(self):
        from duplicate_question_app._evaluation.error_analysis import classify_hardness
        hardness = classify_hardness(
            prob_duplicate=0.95, confidence=0.95, model_agreement=1.0,
            predicted_label=1, true_label=1,
        )
        assert isinstance(hardness, str)


class TestHardMining:
    def test_mine_hard_negatives_embedding_imports(self):
        from duplicate_question_app._evaluation.hard_mining import mine_hard_negatives_embedding
        assert callable(mine_hard_negatives_embedding)

    def test_mine_hard_negatives_lexical_imports(self):
        from duplicate_question_app._evaluation.hard_mining import mine_hard_negatives_lexical
        assert callable(mine_hard_negatives_lexical)

    def test_augment_training_data_imports(self):
        from duplicate_question_app._evaluation.hard_mining import augment_training_data_with_hard_negatives
        assert callable(augment_training_data_with_hard_negatives)
