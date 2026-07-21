from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._routing.routing_context import RoutingContext
from duplicate_question_app._routing.routing_result import RoutingResult


class RoutingPlugin(ABC):
    @abstractmethod
    def process(self, context: RoutingContext, result: RoutingResult) -> RoutingResult: ...


class DefaultRoutingPlugin(RoutingPlugin):
    def process(self, context: RoutingContext, result: RoutingResult) -> RoutingResult:
        return result
