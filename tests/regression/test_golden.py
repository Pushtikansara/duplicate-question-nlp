from __future__ import annotations

import json
from pathlib import Path

import pytest

from duplicate_question_app._models.embeddings import _get_sigmoid_params, _get_threshold, _result_dict

GOLDEN_FILE = Path(__file__).parent / "golden_outputs.json"


@pytest.fixture(scope="session")
def golden_outputs():
    """Load golden (frozen) expected outputs. Creates the file if it doesn't exist."""
    if not GOLDEN_FILE.exists():
        _generate_golden_outputs()
    with open(GOLDEN_FILE) as f:
        return json.load(f)


def _generate_golden_outputs():
    """Generate frozen golden outputs for regression testing."""
    data = {
        "sigmoid_params": {
            "e5-base-v2": {"steepness": 8.0, "midpoint": 0.82},
            "bge-base-en-v1.5": {"steepness": 15.6755, "midpoint": 0.8591},
            "mpnet-base-v2": {"steepness": 11.5976, "midpoint": 0.8133},
        },
        "thresholds": {
            "e5-base-v2": 0.35,
            "bge-base-en-v1.5": 0.3,
            "mpnet-base-v2": 0.36,
        },
        "result_dict": {
            "prediction_duplicate": {
                "predicted_label": 1,
                "prediction": "Duplicate",
                "prob_duplicate": 0.85,
                "prob_non_duplicate": 0.15,
                "confidence": 0.85,
            },
            "prediction_non_duplicate": {
                "predicted_label": 0,
                "prediction": "Non-Duplicate",
                "prob_duplicate": 0.3,
                "prob_non_duplicate": 0.7,
                "confidence": 0.7,
            },
        },
        "model_choices_static": [
            "TF-IDF + Logistic Regression (Week 2)",
            "TF-IDF + Linear SVM (Week 2)",
            "DistilBERT (Week 3)",
            "Improved DistilBERT (Week 4)",
            "BGE-base-en-v1.5",
            "E5-base-v2",
            "E5-quora-finetuned",
            "MPNet-base-v2",
            "DeBERTa-v3 Cross-Encoder",
            "Cross-Encoder-Quora (Trained)",
            "Semantic Ensemble",
        ],
    }
    GOLDEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLDEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


class TestGoldenRegression:
    @pytest.mark.regression
    def test_sigmoid_params_frozen(self, golden_outputs):
        for model_name, expected in golden_outputs["sigmoid_params"].items():
            steepness, midpoint = _get_sigmoid_params(model_name)
            assert steepness == pytest.approx(expected["steepness"], rel=1e-4)
            assert midpoint == pytest.approx(expected["midpoint"], rel=1e-4)

    @pytest.mark.regression
    def test_thresholds_frozen(self, golden_outputs):
        for model_name, expected in golden_outputs["thresholds"].items():
            threshold = _get_threshold(model_name)
            assert threshold == pytest.approx(expected, rel=1e-3)

    @pytest.mark.regression
    def test_result_dict_duplicate_frozen(self, golden_outputs):
        expected = golden_outputs["result_dict"]["prediction_duplicate"]
        result = _result_dict(
            q1="test a",
            q2="test b",
            pred_label=1,
            prob_dup=0.85,
            prob_non=0.15,
            threshold=0.5,
            model_name="E5",
            device="cpu",
            latency_ms=10,
        )
        assert result["predicted_label"] == expected["predicted_label"]
        assert result["prediction"] == expected["prediction"]
        assert result["prob_duplicate"] == pytest.approx(expected["prob_duplicate"])
        assert result["confidence"] == pytest.approx(expected["confidence"])

    @pytest.mark.regression
    def test_result_dict_non_duplicate_frozen(self, golden_outputs):
        expected = golden_outputs["result_dict"]["prediction_non_duplicate"]
        result = _result_dict(
            q1="test a",
            q2="test b",
            pred_label=0,
            prob_dup=0.3,
            prob_non=0.7,
            threshold=0.5,
            model_name="BGE",
            device="cpu",
            latency_ms=5,
        )
        assert result["predicted_label"] == expected["predicted_label"]
        assert result["prediction"] == expected["prediction"]
        assert result["confidence"] == pytest.approx(expected["confidence"])

    @pytest.mark.regression
    def test_model_choices_frozen(self, golden_outputs):
        from duplicate_question_app._config.settings import MODEL_CHOICES

        assert golden_outputs["model_choices_static"] == MODEL_CHOICES
