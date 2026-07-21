from __future__ import annotations

from duplicate_question_app._reasoning.reasoning_graph import DefaultReasoningGraphBuilder
from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
    Premise,
)


class TestReasoningGraph:
    def setup_method(self):
        self.builder = DefaultReasoningGraphBuilder()

    def test_empty_input(self):
        graph = self.builder.build([], [], [])
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_graph_contains_premise_nodes(self):
        premises = [Premise(id="p1", text="test premise", source="test", category="concept")]
        graph = self.builder.build(premises, [], [])
        premise_nodes = [n for n in graph.nodes if n.node_type == "premise"]
        assert len(premise_nodes) == 1
        assert premise_nodes[0].id == "p1"

    def test_graph_contains_hypothesis_nodes(self):
        hypotheses = [Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup hypothesis")]
        graph = self.builder.build([], hypotheses, [])
        hyp_nodes = [n for n in graph.nodes if n.node_type == "hypothesis"]
        assert len(hyp_nodes) == 1

    def test_graph_contains_evidence_nodes(self):
        evidence = [Evidence(id="e1", hypothesis_id="h1", evidence_type=EvidenceType.SUPPORTING, text="evidence")]
        graph = self.builder.build([], [], evidence)
        ev_nodes = [n for n in graph.nodes if n.node_type == "evidence"]
        assert len(ev_nodes) == 1

    def test_graph_edges_connect_premises_to_hypotheses(self):
        premises = [Premise(id="p1", text="premise", source="test", category="concept")]
        hypotheses = [
            Hypothesis(
                id="h1",
                label=HypothesisLabel.DUPLICATE,
                text="hypothesis",
                supporting_premises=["p1"],
            )
        ]
        graph = self.builder.build(premises, hypotheses, [])
        edges = [e for e in graph.edges if e.relation == "supports"]
        assert len(edges) >= 1
        assert edges[0].source_id == "p1"
        assert "h1" in edges[0].target_id

    def test_graph_building_returns_valid_structure(self):
        premises = [Premise(id="p1", text="premise", source="test", category="concept")]
        hypotheses = [Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="hypothesis")]
        evidence = [Evidence(id="e1", hypothesis_id="h1", evidence_type=EvidenceType.SUPPORTING, text="evidence")]
        graph = self.builder.build(premises, hypotheses, evidence)
        assert len(graph.nodes) == 3
        assert len(graph.edges) >= 1
        assert graph.to_dict() is not None
