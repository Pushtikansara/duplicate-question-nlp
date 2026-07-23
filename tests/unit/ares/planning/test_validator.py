from __future__ import annotations

from ares.planning import PlanNode


class TestPlanValidator:
    def test_validate_valid_graph(self, validator, sample_graph, agent_ids) -> None:
        errors = validator.validate(sample_graph, agent_ids)
        assert len(errors) == 0

    def test_is_valid(self, validator, sample_graph, agent_ids) -> None:
        assert validator.is_valid(sample_graph, agent_ids) is True

    def test_validate_missing_agent(self, validator, sample_graph) -> None:
        errors = validator.validate(sample_graph, ["agent-x"])
        assert len(errors) >= 1

    def test_validate_missing_dependency(self, validator, sample_graph, agent_ids) -> None:
        n = PlanNode(node_id="n_bad", goal_id="g1", agent_id="agent-a", action="x", depends_on=["n_missing"])
        sample_graph.add_node(n)
        errors = validator.validate(sample_graph, agent_ids)
        assert any("n_missing" in e for e in errors)

    def test_validate_duplicate_node(self, validator, sample_graph, agent_ids) -> None:
        n = PlanNode(node_id="n1", goal_id="g1", agent_id="agent-a", action="dup")
        from ares.planning.exceptions import DuplicateNodeError

        with __import__("pytest").raises(DuplicateNodeError):
            sample_graph.add_node(n)

    def test_validate_with_tools(self, validator, sample_graph, agent_ids, tool_ids) -> None:
        errors = validator.validate(sample_graph, agent_ids, tool_ids)
        assert len(errors) == 0

    def test_validate_missing_tool(self, validator, sample_graph, agent_ids) -> None:
        n = PlanNode(
            node_id="n_tool",
            goal_id="g1",
            agent_id="agent-a",
            action="x",
            metadata={"required_tools": ["missing-tool"]},
        )
        sample_graph.add_node(n)
        errors = validator.validate(sample_graph, agent_ids, ["tool-fetch"])
        assert any("missing-tool" in e for e in errors)
