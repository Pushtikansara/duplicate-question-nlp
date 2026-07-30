from __future__ import annotations

import dataclasses

import pytest

from ares.orchestration.context import PipelineState, PredictionInput, RequestParams


class TestRequestParams:
    def test_defaults(self):
        params = RequestParams()
        assert params.model is None
        assert params.threshold is None
        assert params.reflect is None
        assert params.skip_cache is False
        assert params.timeout_ms is None

    def test_custom_values(self):
        params = RequestParams(model="test", threshold=0.8, reflect=True, skip_cache=True, timeout_ms=5000.0)
        assert params.model == "test"
        assert params.threshold == 0.8
        assert params.reflect is True
        assert params.skip_cache is True
        assert params.timeout_ms == 5000.0

    def test_immutable(self):
        params = RequestParams()
        with pytest.raises(dataclasses.FrozenInstanceError):
            params.model = "new_model"

    def test_partial(self):
        params = RequestParams(model="custom")
        assert params.model == "custom"
        assert params.threshold is None
        assert params.skip_cache is False


class TestPredictionInput:
    def test_required_fields(self):
        inp = PredictionInput(question1="q1", question2="q2")
        assert inp.question1 == "q1"
        assert inp.question2 == "q2"
        assert isinstance(inp.request_params, RequestParams)

    def test_with_request_params(self):
        params = RequestParams(model="test", threshold=0.9)
        inp = PredictionInput(question1="q1", question2="q2", request_params=params)
        assert inp.request_params.model == "test"
        assert inp.request_params.threshold == 0.9

    def test_immutable(self):
        inp = PredictionInput(question1="q1", question2="q2")
        with pytest.raises(dataclasses.FrozenInstanceError):
            inp.question1 = "modified"

    def test_empty_questions(self):
        inp = PredictionInput(question1="", question2="")
        assert inp.question1 == ""
        assert inp.question2 == ""

    def test_equality(self):
        inp1 = PredictionInput(question1="a", question2="b")
        inp2 = PredictionInput(question1="a", question2="b")
        assert inp1 == inp2

    def test_hashable(self):
        inp = PredictionInput(question1="a", question2="b")
        s = {inp}
        assert len(s) == 1
        inp2 = PredictionInput(question1="a", question2="b")
        s.add(inp2)
        assert len(s) == 1
        inp3 = PredictionInput(question1="c", question2="d")
        s.add(inp3)
        assert len(s) == 2


class TestPipelineState:
    def test_defaults(self):
        state = PipelineState()
        assert state.query_analysis is None
        assert state.engine_config is None
        assert state.prediction_result is None
        assert state.error is None
        assert state.fallback_used is False

    def test_mutable(self):
        state = PipelineState()
        state.error = "something went wrong"
        assert state.error == "something went wrong"
        state.fallback_used = True
        assert state.fallback_used is True

    def test_set_values(self):
        state = PipelineState()
        state.query_analysis = {"key": "value"}
        assert state.query_analysis == {"key": "value"}
        state.engine_config = {"model": "test"}
        assert state.engine_config == {"model": "test"}
        state.prediction_result = {"label": 1}
        assert state.prediction_result == {"label": 1}

    def test_reset(self):
        state = PipelineState()
        state.error = "error"
        state.fallback_used = True
        state.error = None
        state.fallback_used = False
        assert state.error is None
        assert state.fallback_used is False


class TestContextRelationships:
    def test_prediction_input_holds_request_params(self):
        params = RequestParams(skip_cache=True)
        inp = PredictionInput(question1="a", question2="b", request_params=params)
        assert inp.request_params.skip_cache is True
        assert inp.question1 == "a"
        assert inp.question2 == "b"

    def test_pipeline_state_accepts_any_type(self):
        state = PipelineState()
        state.query_analysis = {"complexity": 0.5}
        state.engine_config = {"model": "test"}
        state.prediction_result = {"prediction": "duplicate"}
        assert isinstance(state.query_analysis, dict)
        assert isinstance(state.engine_config, dict)
        assert isinstance(state.prediction_result, dict)


class TestPublicApi:
    def test_all_context_classes_exported(self):
        from ares.orchestration import PipelineState, PredictionInput, RequestParams

        assert PredictionInput is not None
        assert PipelineState is not None
        assert RequestParams is not None
