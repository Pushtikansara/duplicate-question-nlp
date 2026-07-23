from __future__ import annotations

from ares._engine import ARES
from ares._result import PredictionResult
from ares.inference.dispatcher import InferenceDispatcher, predict
from duplicate_question_app import __version__

__all__ = ["ARES", "InferenceDispatcher", "PredictionResult", "predict", "__version__"]
