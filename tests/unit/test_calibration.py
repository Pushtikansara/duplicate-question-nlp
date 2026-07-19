from __future__ import annotations

import numpy as np
import pytest


class TestCalibrationV1:
    def test_calibrate_duplicate_probs_imports(self):
        from duplicate_question_app._calibration.v1 import calibrate_duplicate_probs

        assert callable(calibrate_duplicate_probs)

    def test_calibrate_model_prediction_imports(self):
        from duplicate_question_app._calibration.v1 import calibrate_model_prediction

        assert callable(calibrate_model_prediction)

    def test_temperature_scale_imports(self):
        from duplicate_question_app._calibration.v1 import temperature_scale

        assert callable(temperature_scale)

    def test_platt_scale_imports(self):
        from duplicate_question_app._calibration.v1 import platt_scale

        assert callable(platt_scale)

    def test_get_model_calibration_params_imports(self):
        from duplicate_question_app._calibration.v1 import get_model_calibration_params

        assert callable(get_model_calibration_params)

    def test_calibrate_duplicate_probs_returns_array(self):
        import numpy as np

        from duplicate_question_app._calibration.v1 import calibrate_duplicate_probs

        probs = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        result = calibrate_duplicate_probs(probs, "E5-base-v2")
        assert result is not None


class TestCalibrationV2:
    def test_compute_brier_score_imports(self):
        from duplicate_question_app._calibration.v2 import compute_brier_score

        assert callable(compute_brier_score)

    def test_compute_nll_imports(self):
        from duplicate_question_app._calibration.v2 import compute_nll

        assert callable(compute_nll)

    def test_isotonic_regression_imports(self):
        from duplicate_question_app._calibration.v2 import isotonic_regression

        assert callable(isotonic_regression)

    def test_select_best_calibration_imports(self):
        from duplicate_question_app._calibration.v2 import select_best_calibration

        assert callable(select_best_calibration)

    def test_compute_brier_score_perfect(self):
        from duplicate_question_app._calibration.v2 import compute_brier_score

        y_true = np.array([0, 1, 0, 1])
        y_prob = np.array([0.0, 1.0, 0.0, 1.0])
        brier = compute_brier_score(y_true, y_prob)
        assert brier == pytest.approx(0.0, abs=1e-6)

    def test_compute_nll_finite(self):
        from duplicate_question_app._calibration.v2 import compute_nll

        y_true = np.array([0, 1, 0, 1])
        y_prob = np.array([0.1, 0.9, 0.2, 0.8])
        nll = compute_nll(y_true, y_prob)
        assert np.isfinite(nll)

    def test_select_best_calibration_returns_calibration_result(self):
        from duplicate_question_app._calibration.v2 import select_best_calibration

        y_true = np.array([0, 1, 0, 1])
        y_prob = np.array([0.2, 0.8, 0.3, 0.7])
        result = select_best_calibration(y_true, y_prob)
        assert result is not None
        assert hasattr(result, "method")
        assert hasattr(result, "calibrated_probs")

    def test_isotonic_registration_returns_tuple(self):
        from duplicate_question_app._calibration.v2 import isotonic_regression

        y_true = np.array([0, 1, 0, 1, 0, 1])
        y_prob = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
        calibrator, params = isotonic_regression(y_prob, y_true)
        assert callable(calibrator)
        assert isinstance(params, dict)
