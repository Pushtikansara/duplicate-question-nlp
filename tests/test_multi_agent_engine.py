from __future__ import annotations

import pytest

from ares.agents.agent_selector import DynamicAgentSelector
from ares.agents.cache import SharedCache
from ares.agents.capability_resolver import CapabilityResolver
from ares.agents.decision_agent import DecisionAgent
from ares.agents.execution_context import ExecutionContext
from ares.agents.failure_handler import FailureAction, FailureHandler
from ares.agents.observability import MultiAgentObservability
from ares.agents.task_decomposer import TaskDecomposer
from ares.agents.task_types import AgentTaskType, TaskDecomposition
from ares.agents.tool_discovery import ToolDiscovery
from ares.agents.types import AgentCapability
from ares.tools.registry import ToolRegistry


class TestTaskDecomposer:
    def setup_method(self) -> None:
        self.decomposer = TaskDecomposer()

    def test_decompose_creates_tasks(self) -> None:
        decomp = self.decomposer.decompose("Analyze duplicate questions")
        assert len(decomp.tasks) > 0

    def test_decompose_includes_decision(self) -> None:
        decomp = self.decomposer.decompose("test")
        task_types = {t.task_type for t in decomp.tasks}
        assert AgentTaskType.DECIDE in task_types

    def test_decompose_includes_prediction(self) -> None:
        decomp = self.decomposer.decompose("test")
        task_types = {t.task_type for t in decomp.tasks}
        assert AgentTaskType.PREDICT in task_types

    def test_decompose_dependencies_ordered(self) -> None:
        decomp = self.decomposer.decompose("test")
        task_map = {t.task_id: t for t in decomp.tasks}
        for task in decomp.tasks:
            for dep_id in task.depends_on:
                assert dep_id in task_map, f"Task {task.task_id} depends on unknown {dep_id}"

    def test_decompose_parallel_groups(self) -> None:
        decomp = self.decomposer.decompose("test")
        assert len(decomp.parallel_groups) > 0
        all_ids = {t.task_id for t in decomp.tasks}
        grouped = set()
        for g in decomp.parallel_groups:
            for tid in g:
                grouped.add(tid)
        assert grouped == all_ids

    def test_decompose_no_reflection(self) -> None:
        decomp = self.decomposer.decompose("test", include_reflection=False)
        task_types = {t.task_type for t in decomp.tasks}
        assert AgentTaskType.REFLECT not in task_types

    def test_decompose_no_memory(self) -> None:
        decomp = self.decomposer.decompose("test", include_memory=False)
        task_types = {t.task_type for t in decomp.tasks}
        assert AgentTaskType.MEMORY_STORE not in task_types
        assert AgentTaskType.MEMORY_RETRIEVE not in task_types

    def test_default_decomposition(self) -> None:
        decomp = self.decomposer.create_default_decomposition()
        assert decomp.goal_description == "Analyze semantic similarity between two questions"
        assert len(decomp.tasks) > 0

    def test_to_dict(self) -> None:
        decomp = self.decomposer.decompose("test analysis")
        d = self.decomposer.to_dict(decomp)
        assert d["goal"] == "test analysis"
        assert d["task_count"] == len(decomp.tasks)
        assert len(d["tasks"]) == len(decomp.tasks)


class TestCapabilityResolver:
    def setup_method(self) -> None:
        self.resolver = CapabilityResolver()

    def test_required_capabilities(self) -> None:
        caps = self.resolver.required_capabilities(AgentTaskType.PREDICT)
        assert AgentCapability.PREDICTION in caps

    def test_can_execute_match(self) -> None:
        task = self._make_task(AgentTaskType.PREDICT)
        assert self.resolver.can_execute(task, {AgentCapability.PREDICTION, AgentCapability.SEMANTIC_UNDERSTANDING})

    def test_can_execute_no_match(self) -> None:
        task = self._make_task(AgentTaskType.PREDICT)
        assert not self.resolver.can_execute(task, {AgentCapability.MEMORY})

    def test_rank_agents(self) -> None:
        task = self._make_task(AgentTaskType.PREDICT)
        caps = {
            "agent_a": {AgentCapability.PREDICTION, AgentCapability.SEMANTIC_UNDERSTANDING},
            "agent_b": {AgentCapability.PREDICTION},
            "agent_c": {AgentCapability.MEMORY},
        }
        ranked = self.resolver.rank_agents(task, caps)
        assert ranked[0] == "agent_a"

    def test_best_match(self) -> None:
        task = self._make_task(AgentTaskType.REFLECT)
        caps = {
            "agent_a": {AgentCapability.PREDICTION},
            "agent_b": {AgentCapability.REFLECTION, AgentCapability.CONFIDENCE_ASSESSMENT},
        }
        assert self.resolver.best_match(task, caps) == "agent_b"

    def test_best_match_none(self) -> None:
        task = self._make_task(AgentTaskType.REFLECT)
        assert self.resolver.best_match(task, {}) is None

    def test_list_uncovered(self) -> None:
        tasks = [self._make_task(AgentTaskType.PREDICT), self._make_task(AgentTaskType.REFLECT)]
        caps = {"agent_a": {AgentCapability.PREDICTION}}
        uncovered = self.resolver.list_uncovered(tasks, caps)
        assert AgentTaskType.REFLECT in uncovered

    @staticmethod
    def _make_task(t: AgentTaskType) -> object:
        from ares.agents.task_types import AgentTaskSpec

        return AgentTaskSpec(task_id="t1", task_type=t)


class TestDynamicAgentSelector:
    def test_available_agents_summary_empty(self) -> None:
        selector = DynamicAgentSelector()
        summary = selector.available_agents_summary()
        assert summary["total_active"] == 0


class TestExecutionContext:
    def test_default_creation(self) -> None:
        ctx = ExecutionContext()
        assert ctx.trace_id
        assert ctx.started_at > 0

    def test_phase_timing(self) -> None:
        ctx = ExecutionContext()
        ctx.start_phase("test")
        import time

        time.sleep(0.001)
        elapsed = ctx.end_phase("test")
        assert elapsed > 0
        assert "test_ms" in ctx.phase_timings

    def test_add_task_result(self) -> None:
        ctx = ExecutionContext()
        from ares.agents.task_types import AgentTaskResult

        result = AgentTaskResult(task_id="t1", task_type=AgentTaskType.PREDICT, agent_id="predict", success=True)
        ctx.add_task_result(result)
        assert ctx.get_task_result(AgentTaskType.PREDICT) is not None

    def test_shared_store(self) -> None:
        ctx = ExecutionContext()
        ctx.set("key1", "val1")
        assert ctx.get("key1") == "val1"
        assert ctx.get("nonexistent", "default") == "default"

    def test_summary(self) -> None:
        ctx = ExecutionContext(question1="q1", question2="q2")
        ctx.mark_completed()
        s = ctx.summary()
        assert s["question1"] == "q1"
        assert s["question2"] == "q2"
        assert s["total_time_ms"] >= 0


class TestDecisionAgent:
    @pytest.mark.asyncio
    async def test_execute_basic(self) -> None:
        agent = DecisionAgent()
        output = await agent.execute(
            {
                "prediction": {"confidence": 0.85, "prediction": "duplicate", "predicted_label": 1},
                "reflection": {"trust_score": 0.75},
            }
        )
        assert output.status.name == "SUCCESS"
        assert output.result
        assert "final_confidence" in output.result
        assert output.result["final_confidence"] > 0

    @pytest.mark.asyncio
    async def test_execute_low_confidence(self) -> None:
        agent = DecisionAgent()
        output = await agent.execute(
            {
                "prediction": {"confidence": 0.2, "prediction": "not_duplicate", "predicted_label": 0},
                "reflection": {"trust_score": 0.15},
            }
        )
        assert output.status.name == "SUCCESS"
        assert output.result["recommendations"] == ["manual_review_required"]

    @pytest.mark.asyncio
    async def test_execute_high_trust(self) -> None:
        agent = DecisionAgent()
        output = await agent.execute(
            {
                "prediction": {"confidence": 0.95, "prediction": "duplicate", "predicted_label": 1},
                "reflection": {"trust_score": 0.92},
            }
        )
        assert output.result["recommendations"] == ["automatic_accept"]

    def test_compute_final_confidence(self) -> None:
        agent = DecisionAgent()
        conf = agent._compute_final_confidence(0.9, 0.85, 0.8)
        assert 0.8 <= conf <= 0.9

    def test_temporal_consistency_empty(self) -> None:
        agent = DecisionAgent()
        result = agent._check_temporal_consistency("duplicate", [])
        assert result["consistent"] is True

    def test_temporal_consistency_match(self) -> None:
        agent = DecisionAgent()
        result = agent._check_temporal_consistency(
            "duplicate",
            [
                {"prediction": "duplicate"},
                {"prediction": "duplicate"},
            ],
        )
        assert result["consistent"] is True

    def test_temporal_consistency_mismatch(self) -> None:
        agent = DecisionAgent()
        result = agent._check_temporal_consistency(
            "duplicate",
            [
                {"prediction": "not_duplicate"},
                {"prediction": "not_duplicate"},
            ],
        )
        assert result["consistent"] is False


class TestFailureHandler:
    def setup_method(self) -> None:
        self.handler = FailureHandler(max_global_retries=2)

    def test_retry_action(self) -> None:
        from ares.agents.task_types import AgentTaskResult, AgentTaskSpec

        task = AgentTaskSpec(task_id="t1", task_type=AgentTaskType.PREDICT, max_retries=3)
        result = AgentTaskResult(task_id="t1", task_type=AgentTaskType.PREDICT, agent_id="p", success=False)
        from ares.agents.execution_context import ExecutionContext

        ctx = ExecutionContext()
        action = self.handler.handle_failure(task, result, TaskDecomposition("test"), ctx)
        assert action == FailureAction.RETRY

    def test_skip_on_non_critical(self) -> None:
        self.handler._max_global_retries = 0
        from ares.agents.task_types import AgentTaskResult, AgentTaskSpec

        task = AgentTaskSpec(task_id="t1", task_type=AgentTaskType.SEMANTIC_VALIDATE)
        result = AgentTaskResult(task_id="t1", task_type=AgentTaskType.SEMANTIC_VALIDATE, agent_id="s", success=False)
        from ares.agents.execution_context import ExecutionContext

        ctx = ExecutionContext()
        action = self.handler.handle_failure(task, result, TaskDecomposition("test"), ctx)
        assert action == FailureAction.SKIP

    def test_is_critical(self) -> None:
        assert self.handler.is_critical(AgentTaskType.PREDICT)
        assert self.handler.is_critical(AgentTaskType.DECIDE)
        assert not self.handler.is_critical(AgentTaskType.MEMORY_STORE)

    def test_determine_strategy_timeout(self) -> None:
        action = self.handler.determine_strategy(AgentTaskType.MEMORY_STORE, "timeout after 30s")
        assert action == FailureAction.RETRY

    def test_skip_on_not_found(self) -> None:
        action = self.handler.determine_strategy(AgentTaskType.MEMORY_STORE, "not found")
        assert action == FailureAction.SKIP

    def test_reset(self) -> None:
        self.handler._global_retries["test"] = 1
        self.handler.reset()
        assert len(self.handler._global_retries) == 0


class TestSharedCache:
    def setup_method(self) -> None:
        self.cache = SharedCache(capacity=5)

    def test_set_and_get(self) -> None:
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_expired_entry(self) -> None:
        self.cache.set("key2", "value2", ttl_seconds=-1)
        assert self.cache.get("key2") is None

    def test_has(self) -> None:
        self.cache.set("key3", "value3")
        assert self.cache.has("key3") is True

    def test_has_expired(self) -> None:
        self.cache.set("key4", "value4", ttl_seconds=-1)
        assert self.cache.has("key4") is False

    def test_delete(self) -> None:
        self.cache.set("key5", "value5")
        self.cache.delete("key5")
        assert self.cache.get("key5") is None

    def test_clear(self) -> None:
        self.cache.set("a", "1")
        self.cache.set("b", "2")
        self.cache.clear()
        assert self.cache.size() == 0

    def test_eviction(self) -> None:
        for i in range(10):
            self.cache.set(f"k{i}", f"v{i}")
        assert self.cache.size() <= 5

    def test_stats(self) -> None:
        stats = self.cache.stats()
        assert stats["capacity"] == 5


class TestToolDiscovery:
    def setup_method(self) -> None:
        self.registry = ToolRegistry()
        self.discovery = ToolDiscovery(registry=self.registry)

    def test_required_tools_predict(self) -> None:
        tools = self.discovery.required_tools(AgentTaskType.PREDICT)
        assert "predict" in tools

    def test_required_tools_memory(self) -> None:
        tools = self.discovery.required_tools(AgentTaskType.MEMORY_STORE)
        assert "memory" in tools

    def test_prerequisites_missing(self) -> None:
        missing = self.discovery.check_prerequisites(AgentTaskType.PREDICT)
        assert "predict" in missing

    def test_list_discoverable_empty(self) -> None:
        assert self.discovery.list_discoverable_tools() == []

    def test_find_tools_by_capability(self) -> None:
        assert self.discovery.find_tools_by_capability("predict") == []


class TestMultiAgentObservability:
    def setup_method(self) -> None:
        self.obs = MultiAgentObservability()

    def test_start_tracking(self) -> None:
        self.obs.start_tracking()
        assert self.obs._start_time > 0

    def test_summary_empty(self) -> None:
        s = self.obs.summary()
        assert s["total_tasks"] == 0

    def test_summary_success_rate(self) -> None:
        self.obs.start_tracking()
        from ares.agents.task_types import AgentTaskResult, AgentTaskSpec, AgentTaskType

        task = AgentTaskSpec(task_id="t1", task_type=AgentTaskType.VALIDATE_INPUT, agent_id="a1")
        result = AgentTaskResult(task_id="t1", task_type=AgentTaskType.VALIDATE_INPUT, agent_id="a1", success=True)
        self.obs.record_task_start(task)
        self.obs.record_task_end(task, result)
        s = self.obs.summary()
        assert s["succeeded"] == 1
        assert s["failed"] == 0
        assert s["success_rate"] == 1.0


class TestAgentTaskType:
    def test_enum_values(self) -> None:
        assert AgentTaskType.VALIDATE_INPUT is not None
        assert AgentTaskType.PREDICT is not None
        assert AgentTaskType.DECIDE is not None
        assert AgentTaskType.REFLECT is not None
        assert AgentTaskType.MEMORY_STORE is not None

    def test_task_descriptions(self) -> None:
        from ares.agents.task_types import TASK_DESCRIPTIONS

        assert AgentTaskType.PREDICT in TASK_DESCRIPTIONS
        assert AgentTaskType.DECIDE in TASK_DESCRIPTIONS
        assert len(TASK_DESCRIPTIONS) == len(AgentTaskType)

    def test_tasks_to_capabilities(self) -> None:
        from ares.agents.task_types import TASK_TO_CAPABILITIES

        assert AgentTaskType.PREDICT in TASK_TO_CAPABILITIES
        assert AgentTaskType.MEMORY_STORE in TASK_TO_CAPABILITIES

    def test_task_spec_defaults(self) -> None:
        from ares.agents.task_types import AgentTaskSpec

        spec = AgentTaskSpec(task_id="test", task_type=AgentTaskType.PREDICT)
        assert spec.description
        assert spec.required_capabilities


class TestTaskDecomposition:
    def test_add_result(self) -> None:
        from ares.agents.task_types import AgentTaskResult, AgentTaskType

        decomp = TaskDecomposition("test")
        r = AgentTaskResult(task_id="t1", task_type=AgentTaskType.PREDICT, agent_id="p", success=True)
        decomp.add_result(r)
        assert decomp.get_result(AgentTaskType.PREDICT) is not None

    def test_all_completed(self) -> None:
        from ares.agents.task_types import AgentTaskResult, AgentTaskSpec, AgentTaskType

        decomp = TaskDecomposition("test")
        t = AgentTaskSpec(task_id="t1", task_type=AgentTaskType.VALIDATE_INPUT)
        r = AgentTaskResult(task_id="t1", task_type=AgentTaskType.VALIDATE_INPUT, agent_id="a", success=True)
        decomp.add_task(t)
        decomp.add_result(r)
        assert decomp.all_completed() is True

    def test_success_rate(self) -> None:
        from ares.agents.task_types import AgentTaskResult, AgentTaskType

        decomp = TaskDecomposition("test")
        r1 = AgentTaskResult(task_id="t1", task_type=AgentTaskType.VALIDATE_INPUT, agent_id="a", success=True)
        r2 = AgentTaskResult(task_id="t2", task_type=AgentTaskType.PREDICT, agent_id="a", success=False)
        decomp.add_result(r1)
        decomp.add_result(r2)
        assert decomp.success_rate() == 0.5

    def test_success_rate_empty(self) -> None:
        decomp = TaskDecomposition("test")
        assert decomp.success_rate() == 0.0
