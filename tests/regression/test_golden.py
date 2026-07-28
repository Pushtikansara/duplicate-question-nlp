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
    from ares._config import get_config

    inf_cfg = get_config("inference") or {}
    thresholds = inf_cfg.get("per_model_thresholds", {})
    sigmoid_params = inf_cfg.get("sigmoid_params", {})

    data = {
        "sigmoid_params": {
            "e5-base-v2": {
                "steepness": sigmoid_params.get("E5-base-v2", [8.0, 0.82])[0],
                "midpoint": sigmoid_params.get("E5-base-v2", [8.0, 0.82])[1],
            },
            "bge-base-en-v1.5": {
                "steepness": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591])[0],
                "midpoint": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591])[1],
            },
            "mpnet-base-v2": {
                "steepness": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133])[0],
                "midpoint": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133])[1],
            },
        },
        "thresholds": {
            "e5-base-v2": thresholds.get("E5-base-v2", 0.35),
            "bge-base-en-v1.5": thresholds.get("BGE-base-en-v1.5", 0.3),
            "mpnet-base-v2": thresholds.get("MPNet-base-v2", 0.36),
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
