from __future__ import annotations

from ares._engine import ARES
from ares._result import PredictionResult
from ares.inference.dispatcher import InferenceDispatcher

__version__ = "2.0.0"

__all__ = ["ARES", "InferenceDispatcher", "PredictionResult", "__version__"]
