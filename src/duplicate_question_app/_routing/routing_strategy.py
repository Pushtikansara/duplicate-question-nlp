from __future__ import annotations

from enum import Enum


class RoutingStrategy(Enum):
    FASTEST = "fastest"
    HIGHEST_ACCURACY = "highest_accuracy"
    BALANCED = "balanced"
    RESEARCH = "research"
