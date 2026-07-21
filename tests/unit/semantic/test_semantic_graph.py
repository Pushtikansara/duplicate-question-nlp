"""Tests for SemanticGraph — pure dataclass-based graph."""

from duplicate_question_app._semantic.semantic_graph import SemanticGraph, SemanticNode, SemanticRelation


class TestSemanticGraph:
    def test_empty_graph(self):
        g = SemanticGraph()
        assert g.node_count() == 0
        assert g.edge_count() == 0

    def test_add_node(self):
        g = SemanticGraph()
        n = SemanticNode(id="INSTALL", label="install", node_type="action")
        g.add_node(n)
        assert g.node_count() == 1
        assert g.get_node("INSTALL") is n

    def test_add_edge(self):
        g = SemanticGraph()
        g.add_node(SemanticNode(id="A", label="a", node_type="concept"))
        g.add_node(SemanticNode(id="B", label="b", node_type="concept"))
        e = SemanticRelation(source_id="A", target_id="B", relation_type="related_to")
        g.add_edge(e)
        assert g.edge_count() == 1

    def test_get_edges_for(self):
        g = SemanticGraph()
        g.add_node(SemanticNode(id="A", label="a"))
        g.add_node(SemanticNode(id="B", label="b"))
        g.add_node(SemanticNode(id="C", label="c"))
        g.add_edge(SemanticRelation(source_id="A", target_id="B", relation_type="related_to"))
        g.add_edge(SemanticRelation(source_id="B", target_id="C", relation_type="related_to"))
        assert len(g.get_edges_for("B")) == 2
        assert len(g.get_edges_for("A")) == 1

    def test_get_outgoing_incoming(self):
        g = SemanticGraph()
        g.add_node(SemanticNode(id="A", label="a"))
        g.add_node(SemanticNode(id="B", label="b"))
        g.add_edge(SemanticRelation(source_id="A", target_id="B", relation_type="acts_on"))
        assert len(g.get_outgoing("A")) == 1
        assert len(g.get_incoming("A")) == 0
        assert len(g.get_outgoing("B")) == 0
        assert len(g.get_incoming("B")) == 1

    def test_get_node_nonexistent(self):
        g = SemanticGraph()
        assert g.get_node("NONEXISTENT") is None

    def test_to_dict(self):
        g = SemanticGraph()
        g.add_node(SemanticNode(id="A", label="a", node_type="concept"))
        g.add_edge(SemanticRelation(source_id="A", target_id="A", relation_type="self"))
        d = g.to_dict()
        assert len(d["nodes"]) == 1
        assert len(d["edges"]) == 1
        assert d["nodes"][0]["id"] == "A"

    def test_from_dict(self):
        data = {
            "nodes": [{"id": "X", "label": "x", "type": "concept", "confidence": 0.8}],
            "edges": [{"source": "X", "target": "X", "type": "self", "confidence": 0.9}],
        }
        g = SemanticGraph.from_dict(data)
        assert g.node_count() == 1
        assert g.edge_count() == 1
        assert g.get_node("X") is not None
