from __future__ import annotations

import uuid

from duplicate_question_app._reasoning.interfaces import ReasoningPlugin
from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType, Hypothesis, Premise


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, ReasoningPlugin] = {}

    def register(self, plugin: ReasoningPlugin) -> None:
        self._plugins[plugin.name()] = plugin

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)

    def get(self, name: str) -> ReasoningPlugin | None:
        return self._plugins.get(name)

    def all(self) -> list[ReasoningPlugin]:
        return list(self._plugins.values())

    def process_all(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> list[Evidence]:
        all_new: list[Evidence] = []
        for plugin in self._plugins.values():
            result = plugin.process(premises_a, premises_b, hypotheses, evidence)
            all_new.extend(result)
        return all_new


class ContradictionPlugin(ReasoningPlugin):
    def name(self) -> str:
        return "contradiction_detector"

    def process(
        self,
        premises_a: list[Premise],
        premises_b: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> list[Evidence]:
        result: list[Evidence] = []

        a_entities = {p.text for p in premises_a if p.category == "entity"}
        b_entities = {p.text for p in premises_b if p.category == "entity"}

        for a_ent in a_entities:
            for b_ent in b_entities:
                if a_ent != b_ent:
                    a_keywords = set(a_ent.lower().split())
                    b_keywords = set(b_ent.lower().split())
                    overlap_ratio = len(a_keywords & b_keywords) / max(len(a_keywords | b_keywords), 1)
                    if overlap_ratio > 0.5:
                        for hyp in hypotheses:
                            result.append(
                                Evidence(
                                    id=uuid.uuid4().hex[:12],
                                    hypothesis_id=hyp.id,
                                    evidence_type=EvidenceType.CONTRADICTING,
                                    text=f"Entity contradiction: '{a_ent}' vs '{b_ent}'",
                                    confidence=0.6,
                                    source_premises=[],
                                    weight=0.3,
                                    provenance="ContradictionPlugin",
                                )
                            )

        return result


_default_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
        _default_registry.register(ContradictionPlugin())
    return _default_registry
