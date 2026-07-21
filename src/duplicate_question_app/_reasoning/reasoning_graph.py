from __future__ import annotations

from duplicate_question_app._reasoning.interfaces import ReasoningGraphBuilder
from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    Hypothesis,
    Premise,
    ReasoningEdge,
    ReasoningGraph,
    ReasoningNode,
)


class DefaultReasoningGraphBuilder(ReasoningGraphBuilder):
    def build(
        self,
        premises: list[Premise],
        hypotheses: list[Hypothesis],
        evidence: list[Evidence],
    ) -> ReasoningGraph:
        graph = ReasoningGraph()

        for p in premises:
            graph.add_node(
                ReasoningNode(
                    id=p.id,
                    node_type="premise",
                    label=p.text[:80],
                    confidence=p.confidence,
                    metadata={"category": p.category, "source": p.source},
                )
            )

        for h in hypotheses:
            hyp_node_id = f"hyp_{h.id}"
            graph.add_node(
                ReasoningNode(
                    id=hyp_node_id,
                    node_type="hypothesis",
                    label=h.text[:80],
                    confidence=h.confidence,
                    metadata={"label": h.label.value},
                )
            )

            for premise_id in h.supporting_premises:
                graph.add_edge(
                    ReasoningEdge(
                        source_id=premise_id,
                        target_id=hyp_node_id,
                        relation="supports",
                        confidence=h.confidence,
                    )
                )

            for premise_id in h.contradicting_premises:
                graph.add_edge(
                    ReasoningEdge(
                        source_id=premise_id,
                        target_id=hyp_node_id,
                        relation="contradicts",
                        confidence=h.confidence,
                    )
                )

        for e in evidence:
            ev_node_id = f"ev_{e.id}"
            graph.add_node(
                ReasoningNode(
                    id=ev_node_id,
                    node_type="evidence",
                    label=e.text[:80],
                    confidence=e.confidence,
                    metadata={"evidence_type": e.evidence_type.value, "weight": e.weight},
                )
            )

            hyp_node_id = f"hyp_{e.hypothesis_id}"
            graph.add_edge(
                ReasoningEdge(
                    source_id=hyp_node_id,
                    target_id=ev_node_id,
                    relation="supported_by",
                    confidence=e.confidence,
                )
            )

        return graph
