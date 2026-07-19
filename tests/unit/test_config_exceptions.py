from __future__ import annotations

import pytest

from duplicate_question_app._config.exceptions import (
    ArtifactError,
    CalibrationError,
    ConfigurationError,
    DataError,
    DatasetNotFoundError,
    DuplicateQuestionAppError,
    EnsembleError,
    EvaluationError,
    InferenceError,
    LinguistError,
    ModelNotFoundError,
    ModelNotReadyError,
    PreprocessingError,
    RegistryError,
    TrainingError,
)


class TestExceptionHierarchy:
    def test_all_exceptions_subclass_base(self):
        exceptions = [
            ConfigurationError,
            ModelNotFoundError,
            ModelNotReadyError,
            InferenceError,
            DataError,
            DatasetNotFoundError,
            TrainingError,
            CalibrationError,
            EnsembleError,
            RegistryError,
            EvaluationError,
            PreprocessingError,
            ArtifactError,
            LinguistError,
        ]
        for exc in exceptions:
            assert issubclass(exc, DuplicateQuestionAppError), (
                f"{exc.__name__} is not a subclass of DuplicateQuestionAppError"
            )

    def test_data_error_extends_exception(self):
        assert issubclass(DataError, DuplicateQuestionAppError)

    def test_dataset_not_found_extends_data_error(self):
        assert issubclass(DatasetNotFoundError, DataError)

    def test_exception_instantiation(self):
        exc = DuplicateQuestionAppError("test message")
        assert str(exc) == "test message"

    def test_configuration_error_message(self):
        exc = ConfigurationError("config not found")
        assert "config not found" in str(exc)

    def test_model_not_found_error(self):
        exc = ModelNotFoundError("model missing")
        assert str(exc) == "model missing"

    def test_model_not_ready_error(self):
        exc = ModelNotReadyError("incomplete artifacts")
        assert str(exc) == "incomplete artifacts"

    def test_inference_error(self):
        exc = InferenceError("inference failed")
        assert str(exc) == "inference failed"

    def test_data_error_message(self):
        exc = DataError("data loading failed")
        assert str(exc) == "data loading failed"

    def test_dataset_not_found_error(self):
        exc = DatasetNotFoundError("dataset.parquet not found")
        assert str(exc) == "dataset.parquet not found"

    def test_dataset_not_found_is_data_error(self):
        assert isinstance(DatasetNotFoundError("test"), DataError)

    def test_training_error(self):
        exc = TrainingError("training crashed")
        assert str(exc) == "training crashed"

    def test_calibration_error(self):
        exc = CalibrationError("calibration failed")
        assert str(exc) == "calibration failed"

    def test_ensemble_error(self):
        exc = EnsembleError("ensemble error")
        assert str(exc) == "ensemble error"

    def test_registry_error(self):
        exc = RegistryError("registry corrupt")
        assert str(exc) == "registry corrupt"

    def test_evaluation_error(self):
        exc = EvaluationError("metrics failed")
        assert str(exc) == "metrics failed"

    def test_preprocessing_error(self):
        exc = PreprocessingError("text processing failed")
        assert str(exc) == "text processing failed"

    def test_artifact_error(self):
        exc = ArtifactError("artifact load failed")
        assert str(exc) == "artifact load failed"

    def test_linguist_error(self):
        exc = LinguistError("linguistic analysis failed")
        assert str(exc) == "linguistic analysis failed"

    def test_raise_and_catch_base(self):
        with pytest.raises(DuplicateQuestionAppError):
            raise ConfigurationError("test")

    def test_raise_and_catch_specific(self):
        with pytest.raises(ModelNotFoundError):
            raise ModelNotFoundError("not found")

    def test_raise_and_catch_data_subclass(self):
        with pytest.raises(DataError):
            raise DatasetNotFoundError("missing")

    def test_raise_and_catch_nested(self):
        try:
            raise EnsembleError("outer")
        except DuplicateQuestionAppError as e:
            assert "outer" in str(e)

    def test_exception_with_cause(self):
        try:
            raise RuntimeError("root cause")
        except RuntimeError as cause:
            exc = InferenceError("wrapped")
            exc.__cause__ = cause
            assert exc.__cause__ is cause

    def test_no_extra_exception_classes(self):
        exc_names = {c.__name__ for c in DuplicateQuestionAppError.__subclasses__()}
        expected = {
            "ConfigurationError",
            "ModelNotFoundError",
            "ModelNotReadyError",
            "InferenceError",
            "DataError",
            "TrainingError",
            "CalibrationError",
            "EnsembleError",
            "RegistryError",
            "EvaluationError",
            "PreprocessingError",
            "ArtifactError",
            "LinguistError",
        }
        assert exc_names == expected

    def test_isinstance_check_with_base(self):
        assert isinstance(ModelNotFoundError(), DuplicateQuestionAppError)
        assert isinstance(DataError(), DuplicateQuestionAppError)
        assert isinstance(PreprocessingError(), DuplicateQuestionAppError)
