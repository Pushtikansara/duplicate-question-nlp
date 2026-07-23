from __future__ import annotations

import pytest

from ares.orchestration.exceptions import TaskDependencyError
from ares.orchestration.task_graph import TaskGraph
from ares.orchestration.types import TaskEdge, TaskNode, TaskStatus


class TestTaskGraph:
    def test_add_node(self):
        g = TaskGraph()
        node = TaskNode(id="a", agent_id="agent_a")
        g.add_node(node)
        assert g.has_node("a")
        assert g.node_count() == 1

    def test_add_duplicate_node_raises(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="agent_a"))
        with pytest.raises(TaskDependencyError, match="already exists"):
            g.add_node(TaskNode(id="a", agent_id="agent_b"))

    def test_add_edge(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="agent_a"))
        g.add_node(TaskNode(id="b", agent_id="agent_b"))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))
        assert g.edge_count() == 1

    def test_add_edge_missing_source(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="b", agent_id="agent_b"))
        with pytest.raises(TaskDependencyError, match="not found"):
            g.add_edge(TaskEdge(source_id="a", target_id="b"))

    def test_add_edge_missing_target(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="agent_a"))
        with pytest.raises(TaskDependencyError, match="not found"):
            g.add_edge(TaskEdge(source_id="a", target_id="b"))

    def test_cycle_detection(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b"))
        g.add_node(TaskNode(id="c", agent_id="c"))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))
        g.add_edge(TaskEdge(source_id="b", target_id="c"))
        with pytest.raises(TaskDependencyError, match="cycle"):
            g.add_edge(TaskEdge(source_id="c", target_id="a"))

    def test_get_node(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="agent_a"))
        node = g.get_node("a")
        assert node.id == "a"
        assert node.agent_id == "agent_a"
        assert node.status == TaskStatus.PENDING

    def test_get_node_not_found(self):
        g = TaskGraph()
        with pytest.raises(TaskDependencyError, match="not found"):
            g.get_node("nonexistent")

    def test_get_ready_nodes(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b", depends_on=["a"]))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))

        ready = g.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].id == "a"

        g.update_node_status("a", TaskStatus.COMPLETED)
        ready = g.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].id == "b"

    def test_topological_sort(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b", depends_on=["a"]))
        g.add_node(TaskNode(id="c", agent_id="c", depends_on=["a"]))
        g.add_node(TaskNode(id="d", agent_id="d", depends_on=["b", "c"]))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))
        g.add_edge(TaskEdge(source_id="a", target_id="c"))
        g.add_edge(TaskEdge(source_id="b", target_id="d"))
        g.add_edge(TaskEdge(source_id="c", target_id="d"))

        batches = g.topological_sort()
        assert len(batches) == 3
        assert batches[0] == ["a"]
        assert set(batches[1]) == {"b", "c"}
        assert batches[2] == ["d"]

    def test_topological_sort_with_cycle(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b", depends_on=["b"]))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))
        with pytest.raises(TaskDependencyError, match="cycle"):
            g.add_edge(TaskEdge(source_id="b", target_id="a"))

    def test_update_node_status(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.update_node_status("a", TaskStatus.COMPLETED)
        assert g.get_node("a").status == TaskStatus.COMPLETED

    def test_get_dependents(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b", depends_on=["a"]))
        g.add_node(TaskNode(id="c", agent_id="c", depends_on=["a"]))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))
        g.add_edge(TaskEdge(source_id="a", target_id="c"))

        dependents = g.get_dependents("a")
        assert set(dependents) == {"b", "c"}

    def test_is_complete(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b", depends_on=["a"]))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))

        assert not g.is_complete()
        g.update_node_status("a", TaskStatus.COMPLETED)
        g.update_node_status("b", TaskStatus.COMPLETED)
        assert g.is_complete()

    def test_reset(self):
        g = TaskGraph()
        g.add_node(TaskNode(id="a", agent_id="a"))
        g.add_node(TaskNode(id="b", agent_id="b", depends_on=["a"]))
        g.add_edge(TaskEdge(source_id="a", target_id="b"))
        g.update_node_status("a", TaskStatus.COMPLETED)
        g.update_node_status("b", TaskStatus.FAILED)

        g.reset()
        assert g.get_node("a").status == TaskStatus.PENDING
        assert g.get_node("b").status == TaskStatus.PENDING
        assert g.edge_count() == 0
