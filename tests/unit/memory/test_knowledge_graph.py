from __future__ import annotations

import pytest

from .conftest import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
    create_episodic_memory,
    create_semantic_memory,
)


class TestKnowledgeGraph:
    def test_add_and_get_node(self, knowledge_graph: KnowledgeGraph) -> None:
        node = KnowledgeNode(id="n1", label="Test Node", node_type="concept")
        knowledge_graph.add_node(node)
        retrieved = knowledge_graph.get_node("n1")
        assert retrieved is not None
        assert retrieved.id == "n1"
        assert retrieved.label == "Test Node"

    def test_add_edge(self, knowledge_graph: KnowledgeGraph) -> None:
        n1 = KnowledgeNode(id="a", label="A", node_type="concept")
        n2 = KnowledgeNode(id="b", label="B", node_type="concept")
        knowledge_graph.add_node(n1)
        knowledge_graph.add_node(n2)
        edge = KnowledgeEdge(source_id="a", target_id="b", relation="related_to")
        knowledge_graph.add_edge(edge)
        neighbors = knowledge_graph.get_neighbors("a")
        assert len(neighbors) == 1
        assert neighbors[0][0] == "b"

    def test_get_nonexistent_node(self, knowledge_graph: KnowledgeGraph) -> None:
        assert knowledge_graph.get_node("no-such") is None

    def test_get_neighbors(self, knowledge_graph: KnowledgeGraph) -> None:
        for lid in ["a", "b", "c"]:
            knowledge_graph.add_node(KnowledgeNode(id=lid, label=lid, node_type="concept"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="rel"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="c", relation="rel"))
        neighbors = knowledge_graph.get_neighbors("a")
        assert len(neighbors) == 2

    def test_traverse_depth_1(self, knowledge_graph: KnowledgeGraph) -> None:
        for lid in ["a", "b"]:
            knowledge_graph.add_node(KnowledgeNode(id=lid, label=lid, node_type="concept"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="rel"))
        result = knowledge_graph.traverse("a", max_depth=1)
        assert len(result) == 2
        assert {n.id for n in result} == {"a", "b"}

    def test_traverse_depth_2(self, knowledge_graph: KnowledgeGraph) -> None:
        for lid in ["a", "b", "c"]:
            knowledge_graph.add_node(KnowledgeNode(id=lid, label=lid, node_type="concept"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="rel"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="b", target_id="c", relation="rel"))
        result = knowledge_graph.traverse("a", max_depth=2)
        assert len(result) == 3

    def test_traverse_max_depth(self, knowledge_graph: KnowledgeGraph) -> None:
        for lid in ["a", "b", "c", "d"]:
            knowledge_graph.add_node(KnowledgeNode(id=lid, label=lid, node_type="concept"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="rel"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="b", target_id="c", relation="rel"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="c", target_id="d", relation="rel"))
        result = knowledge_graph.traverse("a", max_depth=1)
        assert len(result) == 2

    def test_search_nodes_by_label(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="py", label="Python", node_type="language"))
        knowledge_graph.add_node(KnowledgeNode(id="js", label="JavaScript", node_type="language"))
        results = knowledge_graph.search_nodes("Python")
        assert len(results) == 1
        assert results[0].id == "py"

    def test_search_nodes_by_type(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="py", label="Python", node_type="language"))
        knowledge_graph.add_node(KnowledgeNode(id="car", label="Car", node_type="object"))
        results = knowledge_graph.search_by_type("language")
        assert len(results) == 1

    def test_to_dict_and_from_dict(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="a", label="A", node_type="type_a", properties={"p": 1}))
        knowledge_graph.add_node(KnowledgeNode(id="b", label="B", node_type="type_b"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="r", weight=0.5))
        data = knowledge_graph.to_dict()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        restored = KnowledgeGraph.from_dict(data)
        assert restored.get_node("a") is not None
        assert len(restored.get_neighbors("a")) == 1

    def test_build_from_memory_empty(self) -> None:
        g = KnowledgeGraph.build_from_memory_entries([])
        assert g.to_dict()["nodes"] == []

    def test_build_from_memory_with_entries(self) -> None:
        entries = [create_episodic_memory(memory_id="e1"), create_semantic_memory(memory_id="e2")]
        g = KnowledgeGraph.build_from_memory_entries(entries)
        assert g.get_node("e1") is not None
        assert g.get_node("e2") is not None

    def test_add_duplicate_node(self, knowledge_graph: KnowledgeGraph) -> None:
        n = KnowledgeNode(id="dup", label="Original", node_type="t")
        knowledge_graph.add_node(n)
        knowledge_graph.add_node(KnowledgeNode(id="dup", label="Overwrite", node_type="t"))
        retrieved = knowledge_graph.get_node("dup")
        assert retrieved is not None
        assert retrieved.label == "Overwrite"

    def test_add_edge_nonexistent_source(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="b", label="B", node_type="t"))
        with pytest.raises(KeyError):
            knowledge_graph.add_edge(KnowledgeEdge(source_id="no-such", target_id="b", relation="r"))

    def test_add_edge_nonexistent_target(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="a", label="A", node_type="t"))
        with pytest.raises(KeyError):
            knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="no-such", relation="r"))

    def test_empty_graph_traverse(self, knowledge_graph: KnowledgeGraph) -> None:
        result = knowledge_graph.traverse("no-such", max_depth=3)
        assert result == []

    def test_graph_cycle_handling(self, knowledge_graph: KnowledgeGraph) -> None:
        for lid in ["a", "b", "c"]:
            knowledge_graph.add_node(KnowledgeNode(id=lid, label=lid, node_type="t"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="r"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="b", target_id="c", relation="r"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="c", target_id="a", relation="r"))
        result = knowledge_graph.traverse("a", max_depth=5)
        assert len(result) == 3

    def test_multiple_edges_between_nodes(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="a", label="A", node_type="t"))
        knowledge_graph.add_node(KnowledgeNode(id="b", label="B", node_type="t"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="r1"))
        knowledge_graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="r2"))
        neighbors = knowledge_graph.get_neighbors("a")
        assert len(neighbors) == 2

    def test_node_properties(self, knowledge_graph: KnowledgeGraph) -> None:
        n = KnowledgeNode(id="prop-node", label="Props", node_type="test", properties={"key": "val", "num": 42})
        knowledge_graph.add_node(n)
        retrieved = knowledge_graph.get_node("prop-node")
        assert retrieved is not None
        assert retrieved.properties["key"] == "val"
        assert retrieved.properties["num"] == 42

    def test_edge_weight(self, knowledge_graph: KnowledgeGraph) -> None:
        knowledge_graph.add_node(KnowledgeNode(id="a", label="A", node_type="t"))
        knowledge_graph.add_node(KnowledgeNode(id="b", label="B", node_type="t"))
        edge = KnowledgeEdge(source_id="a", target_id="b", relation="r", weight=0.75)
        knowledge_graph.add_edge(edge)
        neighbors = knowledge_graph.get_neighbors("a")
        assert neighbors[0][2] == 0.75
