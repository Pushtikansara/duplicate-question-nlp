from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from duplicate_question_app._routing.routing_context import RoutingContext

log = logging.getLogger(__name__)


@dataclass
class RoutingRule:
    name: str
    condition: Callable[[RoutingContext], bool]
    pipeline: str
    priority: int


class RoutingRulesEngine:
    def __init__(self, rules: list[RoutingRule] | None = None):
        self._rules: list[RoutingRule] = list(rules) if rules else []

    def evaluate(self, context: RoutingContext) -> list[RoutingRule]:
        matched: list[RoutingRule] = []
        for rule in sorted(self._rules, key=lambda r: r.priority, reverse=True):
            try:
                if rule.condition(context):
                    matched.append(rule)
            except Exception:
                log.exception("Routing rule '%s' raised an exception during evaluation", rule.name)
        return matched

    def add_rule(self, rule: RoutingRule) -> None:
        self._rules.append(rule)
