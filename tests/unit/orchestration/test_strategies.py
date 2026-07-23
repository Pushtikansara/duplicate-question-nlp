from __future__ import annotations

import pytest

from ares.orchestration.strategies.debate import DebateStrategy
from ares.orchestration.strategies.hierarchical import HierarchicalStrategy
from ares.orchestration.strategies.parallel import ParallelStrategy
from ares.orchestration.strategies.pipeline import PipelineStrategy
from ares.orchestration.strategies.sequential import SequentialStrategy
from ares.orchestration.strategies.supervisor import SupervisorStrategy
from ares.orchestration.strategies.voting import VotingStrategy
from ares.orchestration.types import (
    OrchestrationStatus,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
)


class BaseStrategyTest:
    strategy_cls = None
    strategy_type = None

    @pytest.fixture
    def strategy(self):
        return self.strategy_cls()

    @pytest.fixture
    def shared_context(self):
        return SharedAgentContext(workflow_id="test_wf", trace_id="trace_1")

    def test_strategy_type(self, strategy):
        assert strategy.strategy_type == self.strategy_type


class TestSequentialStrategy(BaseStrategyTest):
    strategy_cls = SequentialStrategy
    strategy_type = OrchestrationStrategyType.SEQUENTIAL

    async def test_sequential_execution(self, strategy, success_agent, success_agent_b, failing_agent, shared_context):
        result = await strategy.execute(
            agents=[success_agent, success_agent_b],
            input={"query": "test"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_sequential_stops_on_error(
        self, strategy, success_agent, success_agent_b, failing_agent, shared_context
    ):
        result = await strategy.execute(
            agents=[success_agent, failing_agent, success_agent_b],
            input={"query": "test"},
            shared_context=shared_context,
            policies=RunPolicies(stop_on_first_error=True),
        )
        assert len(result.agent_results) == 1

    async def test_sequential_empty_agents(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_sequential_sends_input_chain(self, strategy, success_agent, success_agent_b, shared_context):
        result = await strategy.execute(
            agents=[success_agent, success_agent_b],
            input={"initial": "data"},
            shared_context=shared_context,
        )
        assert len(result.agent_results) == 2


class TestParallelStrategy(BaseStrategyTest):
    strategy_cls = ParallelStrategy
    strategy_type = OrchestrationStrategyType.PARALLEL

    async def test_parallel_execution(self, strategy, success_agent, success_agent_b, success_agent_c, shared_context):
        result = await strategy.execute(
            agents=[success_agent, success_agent_b, success_agent_c],
            input={"query": "test"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 3

    async def test_parallel_partial_failure(
        self, strategy, success_agent, success_agent_b, failing_agent, shared_context
    ):
        result = await strategy.execute(
            agents=[success_agent, failing_agent, success_agent_b],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.PARTIAL
        assert len(result.agent_results) == 2

    async def test_parallel_empty(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_parallel_with_concurrency_limit(
        self, strategy, success_agent, success_agent_b, success_agent_c, shared_context
    ):
        policies = RunPolicies(max_concurrency=2)
        result = await strategy.execute(
            agents=[success_agent, success_agent_b, success_agent_c],
            input={"query": "test"},
            shared_context=shared_context,
            policies=policies,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 3


class TestHierarchicalStrategy(BaseStrategyTest):
    strategy_cls = HierarchicalStrategy
    strategy_type = OrchestrationStrategyType.HIERARCHICAL

    async def test_hierarchical_execution(self, strategy, supervisor_agent, worker_a, worker_b, shared_context):
        result = await strategy.execute(
            agents=[supervisor_agent, worker_a, worker_b],
            input={"task": "analyze"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) >= 1

    async def test_hierarchical_no_workers(self, strategy, supervisor_agent, shared_context):
        result = await strategy.execute(
            agents=[supervisor_agent],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_hierarchical_empty(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED


class TestDebateStrategy(BaseStrategyTest):
    strategy_cls = DebateStrategy
    strategy_type = OrchestrationStrategyType.DEBATE

    async def test_debate_execution(self, strategy, success_agent, success_agent_b, shared_context):
        result = await strategy.execute(
            agents=[success_agent, success_agent_b],
            input={"topic": "test"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 2

    async def test_debate_sends_messages(self, strategy, success_agent, success_agent_b, shared_context):
        _ = await strategy.execute(
            agents=[success_agent, success_agent_b],
            input={"topic": "test"},
            shared_context=shared_context,
        )
        assert len(shared_context.messages) > 0

    async def test_debate_single_agent(self, strategy, success_agent, shared_context):
        result = await strategy.execute(
            agents=[success_agent],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_debate_empty(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_debate_builds_consensus(self, strategy, success_agent, success_agent_b, shared_context):
        _ = await strategy.execute(
            agents=[success_agent, success_agent_b],
            input={"topic": "test"},
            shared_context=shared_context,
        )
        consensus = shared_context.get("consensus")
        assert consensus is not None
        assert "consensus" in consensus
        assert "agreement" in consensus


class TestVotingStrategy(BaseStrategyTest):
    strategy_cls = VotingStrategy
    strategy_type = OrchestrationStrategyType.VOTING

    async def test_voting_majority(self, strategy, vote_agent_yes, shared_context):
        result = await strategy.execute(
            agents=[vote_agent_yes, vote_agent_yes],
            input={"question": "test"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_voting_tally(self, strategy, vote_agent_yes, vote_agent_no, shared_context):
        _ = await strategy.execute(
            agents=[vote_agent_yes, vote_agent_no],
            input={"question": "test"},
            shared_context=shared_context,
        )
        vote_result = shared_context.get("vote_result")
        assert vote_result is not None
        assert vote_result["total_votes"] == 2
        assert "winner" in vote_result

    async def test_voting_empty(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_voting_require_majority(self, strategy, vote_agent_yes, vote_agent_no, shared_context):
        strategy._require_majority = True
        _ = await strategy.execute(
            agents=[vote_agent_yes, vote_agent_no],
            input={"question": "test"},
            shared_context=shared_context,
        )
        vote_result = shared_context.get("vote_result")
        assert vote_result is not None

    async def test_voting_min_votes_not_met(self, strategy, vote_agent_yes, shared_context):
        strategy._min_votes = 3
        _ = await strategy.execute(
            agents=[vote_agent_yes, vote_agent_yes],
            input={},
            shared_context=shared_context,
        )
        vote_result = shared_context.get("vote_result")
        assert vote_result["winner"] is None

    async def test_voting_high_confidence_wins(self, strategy, vote_agent_yes, vote_agent_no, shared_context):
        _ = await strategy.execute(
            agents=[vote_agent_yes, vote_agent_no],
            input={},
            shared_context=shared_context,
        )
        vote_result = shared_context.get("vote_result")
        assert vote_result["winner"] == "yes"
        assert vote_result["confidence"] > 0.5


class TestPipelineStrategy(BaseStrategyTest):
    strategy_cls = PipelineStrategy
    strategy_type = OrchestrationStrategyType.PIPELINE

    async def test_pipeline_execution(self, strategy, success_agent, success_agent_b, success_agent_c, shared_context):
        result = await strategy.execute(
            agents=[success_agent, success_agent_b, success_agent_c],
            input={"query": "test"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED
        assert len(result.agent_results) == 3

    async def test_pipeline_with_stage_map(self, success_agent, success_agent_b, shared_context):
        strategy = PipelineStrategy(
            stage_map={
                "stage_1": ["success_agent"],
                "stage_2": ["success_agent_b"],
            }
        )
        result = await strategy.execute(
            agents=[success_agent, success_agent_b],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_pipeline_stops_on_error(
        self, strategy, success_agent, success_agent_b, failing_agent, shared_context
    ):
        policies = RunPolicies(stop_on_first_error=True)
        result = await strategy.execute(
            agents=[success_agent, failing_agent, success_agent_b],
            input={},
            shared_context=shared_context,
            policies=policies,
        )
        assert len(result.agent_results) == 1
        assert result.agent_results[0].agent_id == "success_agent"
        assert result.status == OrchestrationStatus.PARTIAL

    async def test_pipeline_empty(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_pipeline_skips_on_failure(self, strategy, failing_agent, success_agent, shared_context):
        result = await strategy.execute(
            agents=[failing_agent, success_agent],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.PARTIAL


class TestSupervisorStrategy(BaseStrategyTest):
    strategy_cls = SupervisorStrategy
    strategy_type = OrchestrationStrategyType.SUPERVISOR

    async def test_supervisor_execution(self, strategy, supervisor_agent, worker_a, worker_b, shared_context):
        result = await strategy.execute(
            agents=[supervisor_agent, worker_a, worker_b],
            input={"task": "analyze"},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_supervisor_fewer_than_two(self, strategy, supervisor_agent, shared_context):
        result = await strategy.execute(
            agents=[supervisor_agent],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_supervisor_empty(self, strategy, shared_context):
        result = await strategy.execute(
            agents=[],
            input={},
            shared_context=shared_context,
        )
        assert result.status == OrchestrationStatus.COMPLETED

    async def test_supervisor_sends_messages(self, strategy, supervisor_agent, worker_a, worker_b, shared_context):
        _ = await strategy.execute(
            agents=[supervisor_agent, worker_a, worker_b],
            input={"task": "analyze"},
            shared_context=shared_context,
        )
        assert len(shared_context.messages) >= 2
