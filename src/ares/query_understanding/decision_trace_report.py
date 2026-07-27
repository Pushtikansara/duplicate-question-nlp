from __future__ import annotations

from ares.query_understanding.decision_trace_models import DecisionTrace
from ares.query_understanding.decision_trace_renderer import DecisionTraceRenderer


class DecisionTraceReport:
    def __init__(self) -> None:
        self._renderer = DecisionTraceRenderer()

    def generate_human(self, trace: DecisionTrace) -> str:
        return self._renderer.render_plaintext(trace)

    def generate_developer(self, trace: DecisionTrace) -> str:
        return self._renderer.render_json(trace)

    def generate_machine(self, trace: DecisionTrace) -> dict:
        return self._renderer.render_dict(trace)

    def generate_markdown(self, trace: DecisionTrace) -> str:
        return self._renderer.render_markdown(trace)
