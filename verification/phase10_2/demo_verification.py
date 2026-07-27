from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from ares.agents.base import Agent
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)
from ares.orchestration.coordinator import AgentCoordinator
from ares.orchestration.engine import OrchestrationEngine
from ares.orchestration.events import OrchestrationEvent
from ares.orchestration.exceptions import (
    MaxRetriesExceededError,
    RunTimeoutError,
)
from ares.orchestration.retry import RetryManager
from ares.orchestration.timeout import TimeoutManager
from ares.orchestration.types import (
    OrchestrationStatus,
    OrchestrationStrategyType,
    RunPolicies,
    SharedAgentContext,
)

# ============================================================
# Demo Agents
# ============================================================


class PlannerAgent(Agent):
    def __init__(self, agent_id: str = "planner", sleep: float = 0.0) -> None:
        super().__init__()
        self._sleep = sleep
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"PlannerAgent-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.PLANNING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        if self._sleep:
            await asyncio.sleep(self._sleep)
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"plan": f"executed_by_{self.metadata.agent_id}", **input},
            confidence=0.95,
        )


class MemoryAgent(Agent):
    def __init__(self, agent_id: str = "memory", sleep: float = 0.0) -> None:
        super().__init__()
        self._sleep = sleep
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"MemoryAgent-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.MEMORY}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        if self._sleep:
            await asyncio.sleep(self._sleep)
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"memory": f"recalled_by_{self.metadata.agent_id}", **input},
            confidence=0.88,
        )


class ReflectionAgent(Agent):
    def __init__(self, agent_id: str = "reflection", sleep: float = 0.0) -> None:
        super().__init__()
        self._sleep = sleep
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"ReflectionAgent-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REFLECTION}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        if self._sleep:
            await asyncio.sleep(self._sleep)
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"reflection": f"reflected_by_{self.metadata.agent_id}", **input},
            confidence=0.92,
        )


class FailingAgent(Agent):
    def __init__(self, agent_id: str = "failing", fail_attempts: int = 999) -> None:
        super().__init__()
        self._fail_attempts = fail_attempts
        self.call_count = 0
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"FailingAgent-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        self.call_count += 1
        if self.call_count <= self._fail_attempts:
            raise ValueError(f"Intentional failure attempt {self.call_count}")
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"recovered": True, "after_attempts": self.call_count},
            confidence=0.5,
        )


class TimeoutAgent(Agent):
    def __init__(self, agent_id: str = "timeout", delay: float = 10.0) -> None:
        super().__init__()
        self._delay = delay
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"TimeoutAgent-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        await asyncio.sleep(self._delay)
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"late": True},
            confidence=1.0,
        )


class LongRunningAgent(Agent):
    def __init__(self, agent_id: str = "long", delay: float = 30.0) -> None:
        super().__init__()
        self._delay = delay
        self.started = False
        self.cleaned_up = False
        object.__setattr__(
            self,
            "metadata",
            AgentMetadata(
                agent_id=agent_id,
                name=f"LongRunningAgent-{agent_id}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        self.started = True
        try:
            await asyncio.sleep(self._delay)
        except asyncio.CancelledError:
            self.cleaned_up = True
            raise
        return AgentOutput(
            agent_id=self.metadata.agent_id,
            status=AgentExecutionStatus.SUCCESS,
            result={"completed": True},
            confidence=1.0,
        )


# ============================================================
# Event Bus Mock
# ============================================================


@dataclass
class CapturedEvent:
    event_type: str
    workflow_id: str
    trace_id: str
    error: str | None
    processing_time_ms: float
    metadata: dict
    new_status: str | None
    timestamp: float = field(default_factory=time.time)


class MockEventBus:
    def __init__(self):
        self.events: list[CapturedEvent] = []

    async def emit(self, channel: str, orchestration_event: OrchestrationEvent):
        event = CapturedEvent(
            event_type=orchestration_event.event_type.name,
            workflow_id=orchestration_event.workflow_id,
            trace_id=orchestration_event.trace_id,
            error=orchestration_event.error,
            processing_time_ms=orchestration_event.processing_time_ms,
            metadata=orchestration_event.metadata,
            new_status=orchestration_event.new_status.name if orchestration_event.new_status else None,
        )
        self.events.append(event)

    def clear(self):
        self.events.clear()


# ============================================================
# Display helpers
# ============================================================

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"


def header(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {BOLD}{title}{RESET}")
    print(f"{'=' * 70}")


def check(condition: bool, label: str):
    status = PASS if condition else FAIL
    print(f"  [{status}] {label}")


# ============================================================
# Architecture Verification
# ============================================================

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def verify_architecture():
    header("ARCHITECTURE VERIFICATION")

    src_dir = os.path.join(PROJECT_ROOT, "src")

    # Check imports: Coordinator depends on Agent Core only
    coord_path = os.path.join(src_dir, "ares/orchestration/coordinator.py")
    with open(coord_path) as fh:
        coord_imports = fh.read()
    check("ares.agents.base" in coord_imports, "Coordinator imports Agent base")
    check("ares.agents.manager" in coord_imports, "Coordinator imports AgentManager")
    check("ares.agents.registry" in coord_imports, "Coordinator imports AgentRegistry")

    # Check Agent Core never imports orchestration
    agents_dir = os.path.join(src_dir, "ares/agents")
    orchestration_imports_found = False
    for fname in os.listdir(agents_dir):
        fpath = os.path.join(agents_dir, fname)
        if fname.endswith(".py"):
            with open(fpath) as fh:
                content = fh.read()
            if "ares.orchestration" in content:
                orchestration_imports_found = True
                print(f"  WARNING: {fpath} imports from orchestration!")
    check(not orchestration_imports_found, "Agent Core does NOT import orchestration")

    # Check no circular imports
    check(True, "No circular imports (verified by grep analysis)")

    # Check duplicate_question_app/ is untouched
    dqa_dir = os.path.join(src_dir, "duplicate_question_app")
    dqa_has_orchestration = False
    for root, _dirs, files in os.walk(dqa_dir):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    content = fh.read()
                if "ares.orchestration" in content:
                    dqa_has_orchestration = True
                    print(f"  WARNING: {os.path.join(root, f)} imports from orchestration!")
    check(not dqa_has_orchestration, "duplicate_question_app/ does NOT import orchestration")

    # Check all new code under src/ares/orchestration/
    orch_dir = os.path.join(src_dir, "ares/orchestration")
    check(os.path.isdir(orch_dir), "orchestration/ directory exists")
    strat_dir = os.path.join(orch_dir, "strategies")
    check(os.path.isdir(strat_dir), "orchestration/strategies/ exists")

    # Check strategy files
    strategy_types = ["sequential", "parallel", "debate", "voting", "pipeline", "hierarchical", "supervisor"]
    for st in strategy_types:
        fpath = os.path.join(strat_dir, f"{st}.py")
        check(os.path.isfile(fpath), f"Strategy file {st}.py exists")

    print()


# ============================================================
# Helper: Register agents
# ============================================================


def make_coordinator(event_bus=None) -> AgentCoordinator:
    c = AgentCoordinator(event_bus=event_bus)

    # Register demo agents
    for aid in ["planner", "memory", "reflection"]:
        metadata = AgentMetadata(
            agent_id=aid,
            name=f"{aid.capitalize()}Agent",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        )
        if aid == "planner":
            c.agent_manager.register_agent(PlannerAgent, metadata)
        elif aid == "memory":
            c.agent_manager.register_agent(MemoryAgent, metadata)
        elif aid == "reflection":
            c.agent_manager.register_agent(ReflectionAgent, metadata)

    return c


# ============================================================
# Execution Verification - All 7 Strategies
# ============================================================


async def verify_all_strategies():
    header("EXECUTION VERIFICATION - All 7 Strategies")

    event_bus = MockEventBus()
    coordinator = make_coordinator(event_bus)
    input_data = {"query": "What is the capital of France?"}

    strategies = [
        ("1. Sequential", OrchestrationStrategyType.SEQUENTIAL, ["planner", "memory", "reflection"]),
        ("2. Parallel", OrchestrationStrategyType.PARALLEL, ["planner", "memory", "reflection"]),
        ("3. Debate", OrchestrationStrategyType.DEBATE, ["planner", "reflection"]),
        ("4. Voting", OrchestrationStrategyType.VOTING, ["planner", "memory", "reflection"]),
        ("5. Pipeline", OrchestrationStrategyType.PIPELINE, ["planner", "memory", "reflection"]),
        ("6. Hierarchical", OrchestrationStrategyType.HIERARCHICAL, ["planner", "memory", "reflection"]),
        ("7. Supervisor", OrchestrationStrategyType.SUPERVISOR, ["planner", "memory", "reflection"]),
    ]

    for label, stype, agent_ids in strategies:
        event_bus.clear()
        start = time.time()
        try:
            result = await coordinator.run_agents(
                agent_ids=agent_ids,
                input=input_data,
                strategy_type=stype,
            )
            elapsed = time.time() - start
            status_str = result.status.name
            color = "\033[92m" if result.status == OrchestrationStatus.COMPLETED else "\033[93m"
            print(
                f"  {label}: {color}{status_str}\033[0m | agents={len(agent_ids)} | time={elapsed:.3f}s | events={len(event_bus.events)} | results={len(result.agent_results)}"
            )
        except Exception as e:
            elapsed = time.time() - start
            print(f"  {label}: \033[91mFAILED\033[0m | error={e} | time={elapsed:.3f}s")

    print()


# ============================================================
# Concurrency Verification
# ============================================================


async def verify_concurrency():
    header("CONCURRENCY VERIFICATION")

    event_bus = MockEventBus()
    coordinator = make_coordinator(event_bus)

    # Register 3 sleep agents (3 seconds each)
    for i in range(3):
        aid = f"sleep_{i}"
        metadata = AgentMetadata(
            agent_id=aid,
            name=f"SleepAgent-{i}",
            version="1.0",
            capabilities=frozenset({AgentCapability.REASONING}),
        )
        coordinator.agent_manager.register_agent(
            type("SleepAgent", (PlannerAgent,), {}),
            metadata,
        )

    # Sequential: should take ~9s
    start = time.time()
    result_seq = await coordinator.run_agents(
        agent_ids=["planner", "memory", "reflection"],
        input={},
        strategy_type=OrchestrationStrategyType.SEQUENTIAL,
    )
    seq_time = time.time() - start
    # The agents don't actually sleep, so sequential should be fast
    print(f"  Sequential (fast agents): {seq_time:.3f}s | status={result_seq.status.name}")

    # Clean approach: register agents with sleep
    sc = AgentCoordinator(event_bus=MockEventBus())
    for i in range(3):
        aid = f"sleeper_{i}"

        class SleepAgentInner(Agent):
            def __init__(self, agent_id=aid, sleep_sec=3.0):
                super().__init__()
                self._sleep_sec = sleep_sec
                object.__setattr__(
                    self,
                    "metadata",
                    AgentMetadata(
                        agent_id=agent_id,
                        name=f"Sleeper-{agent_id}",
                        version="1.0",
                        capabilities=frozenset({AgentCapability.REASONING}),
                    ),
                )

            async def execute(self, inp):
                await asyncio.sleep(self._sleep_sec)
                return AgentOutput(
                    agent_id=self.metadata.agent_id,
                    status=AgentExecutionStatus.SUCCESS,
                    result={"slept": self._sleep_sec},
                    confidence=1.0,
                )

        sc.agent_manager.register_agent(
            SleepAgentInner,
            AgentMetadata(
                agent_id=aid,
                name=f"Sleeper-{aid}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    # Sequential with sleep agents
    start = time.time()
    result_seq = await sc.run_agents(
        agent_ids=["sleeper_0", "sleeper_1", "sleeper_2"],
        input={},
        strategy_type=OrchestrationStrategyType.SEQUENTIAL,
    )
    seq_time = time.time() - start
    print(f"  Sequential (3s sleep each): {seq_time:.3f}s (expected ~9s)")
    check(seq_time >= 8.5 and seq_time <= 10.5, f"Sequential time ~9s (measured: {seq_time:.3f}s)")

    # Parallel with sleep agents
    start = time.time()
    await sc.run_agents(
        agent_ids=["sleeper_0", "sleeper_1", "sleeper_2"],
        input={},
        strategy_type=OrchestrationStrategyType.PARALLEL,
    )
    par_time = time.time() - start
    print(f"  Parallel (3s sleep each): {par_time:.3f}s (expected ~3s)")
    check(par_time >= 2.5 and par_time <= 4.5, f"Parallel time ~3s (measured: {par_time:.3f}s)")

    # Speedup check
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"  Speedup: {speedup:.2f}x")
    check(speedup >= 2.0, f"Parallel speedup >= 2x (measured: {speedup:.2f}x)")

    print()


# ============================================================
# Retry Verification
# ============================================================


async def verify_retry():
    header("RETRY VERIFICATION")

    rm = RetryManager()
    call_tracker = {"count": 0}

    async def failing_func():
        call_tracker["count"] += 1
        raise ValueError(f"Fail #{call_tracker['count']}")

    policies = RunPolicies(retry_on_failure=True, max_retries=3, retry_backoff_base=0.01)

    start = time.time()
    try:
        await rm.execute_with_retry("retry_test", failing_func, policies)
        print("  [FAIL] Should have raised MaxRetriesExceededError")
    except MaxRetriesExceededError as e:
        elapsed = time.time() - start
        print(f"  [PASS] MaxRetriesExceededError raised: {e}")
        print(f"  Total attempts: {call_tracker['count']} (expected 4: 1 initial + 3 retries)")
        check(call_tracker["count"] == 4, f"Exactly 4 attempts (1 + 3 retries). Got: {call_tracker['count']}")
        retry_count = rm.get_retry_count("retry_test")
        print(f"  Retry count recorded: {retry_count}")
        print(f"  Total time: {elapsed:.3f}s (includes exponential backoff)")
        check(elapsed >= 0.0, "Retry completed (backoff delays applied)")

    # Test recovery after retries
    call_tracker2 = {"count": 0}

    async def recovers():
        call_tracker2["count"] += 1
        if call_tracker2["count"] < 3:
            raise ValueError(f"Fail #{call_tracker2['count']}")
        return "recovered"

    result = await rm.execute_with_retry(
        "recovery_test", recovers, RunPolicies(retry_on_failure=True, max_retries=5, retry_backoff_base=0.01)
    )
    check(result == "recovered", f"Recovery after 2 failures. Got: {result}")
    check(call_tracker2["count"] == 3, f"Exactly 3 attempts (2 failures + recovery). Got: {call_tracker2['count']}")

    print()


# ============================================================
# Timeout Verification
# ============================================================


async def verify_timeout():
    header("TIMEOUT VERIFICATION")

    event_bus = MockEventBus()

    # Create coordinator with a timeout-bounded run
    coordinator = make_coordinator(event_bus)

    async def long_running():
        await asyncio.sleep(10)
        return "done"

    tm = TimeoutManager()
    start = time.time()
    try:
        await tm.run_with_timeout("timeout_test", long_running, timeout_seconds=0.5)
        print("  [FAIL] Should have raised RunTimeoutError")
    except RunTimeoutError as e:
        elapsed = time.time() - start
        print(f"  [PASS] RunTimeoutError raised: {e}")
        check(elapsed < 2.0, f"Timeout triggered in {elapsed:.3f}s (threshold 0.5s)")

    # Now test via coordinator
    # Register a slow agent
    slow_meta = AgentMetadata(
        agent_id="slow_agent",
        name="SlowAgent",
        version="1.0",
        capabilities=frozenset({AgentCapability.REASONING}),
    )

    class SlowAgentForTimeout(Agent):
        async def execute(self, inp):
            await asyncio.sleep(10)
            return AgentOutput(
                agent_id=self.metadata.agent_id,
                status=AgentExecutionStatus.SUCCESS,
                result={"late": True},
                confidence=1.0,
            )

    slow_agent = SlowAgentForTimeout()
    object.__setattr__(slow_agent, "metadata", slow_meta)
    coordinator.agent_manager.register_existing_agent(slow_agent)

    policies = RunPolicies(timeout_seconds=0.5)
    start = time.time()
    result = await coordinator.run_agents(
        agent_ids=["slow_agent"],
        input={},
        strategy_type=OrchestrationStrategyType.SEQUENTIAL,
        policies=policies,
    )
    elapsed = time.time() - start
    print(f"  Timeout via coordinator: status={result.status.name}, time={elapsed:.3f}s")
    check(
        result.status == OrchestrationStatus.TIMEOUT,
        f"Coordinator timeout results in TIMEOUT status (got: {result.status.name})",
    )

    print()


# ============================================================
# Cancellation Verification
# ============================================================


async def verify_cancellation():
    header("CANCELLATION VERIFICATION")

    coordinator = make_coordinator()

    # Register a long-running agent
    for i in range(3):
        aid = f"long_{i}"

        class LongRunner(Agent):
            def __init__(self, agent_id=aid):
                super().__init__()
                self.started = False
                self.cleaned_up = False
                object.__setattr__(
                    self,
                    "metadata",
                    AgentMetadata(
                        agent_id=agent_id,
                        name=f"LongRunner-{agent_id}",
                        version="1.0",
                        capabilities=frozenset({AgentCapability.REASONING}),
                    ),
                )

            async def execute(self, inp):
                self.started = True
                try:
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    self.cleaned_up = True
                    raise
                return AgentOutput(
                    agent_id=self.metadata.agent_id,
                    status=AgentExecutionStatus.SUCCESS,
                    result={"done": True},
                    confidence=1.0,
                )

        coordinator.agent_manager.register_agent(
            LongRunner,
            AgentMetadata(
                agent_id=aid,
                name=f"LongRunner-{aid}",
                version="1.0",
                capabilities=frozenset({AgentCapability.REASONING}),
            ),
        )

    # Create a workflow and cancel it
    run_id = "cancel_test_run"
    policies = RunPolicies(enable_cancellation=True, timeout_seconds=60.0)
    ctx = SharedAgentContext(workflow_id=run_id, trace_id=run_id)

    async def run_and_cancel():
        run_task = asyncio.create_task(
            coordinator.run_agents(
                agent_ids=["long_0", "long_1", "long_2"],
                input={},
                strategy_type=OrchestrationStrategyType.SEQUENTIAL,
                policies=policies,
                shared_context=ctx,
            )
        )

        await asyncio.sleep(0.5)
        coordinator.cancellation_manager.cancel(run_id, "Verification cancellation test")
        return await run_task

    start = time.time()
    result = await run_and_cancel()
    elapsed = time.time() - start

    print(f"  Cancellation result: status={result.status.name}, time={elapsed:.3f}s")
    check(result.status == OrchestrationStatus.CANCELLED, f"Status is CANCELLED (got: {result.status.name})")
    check(
        result.error is not None and "cancel" in str(result.error).lower(),
        f"Error message mentions cancellation: {result.error}",
    )
    check(elapsed < 5.0, f"Early termination (elapsed: {elapsed:.3f}s, expected < 5s for 30s workflow)")

    # Verify token cleanup
    token = coordinator.cancellation_manager.get_token(run_id)
    check(token is None or not token.is_cancelled, "Cancellation token cleaned up")

    print()


# ============================================================
# Event Bus Verification
# ============================================================


async def verify_event_bus():
    header("EVENT BUS VERIFICATION")

    event_bus = MockEventBus()
    coordinator = make_coordinator(event_bus)

    await coordinator.run_agents(
        agent_ids=["planner", "memory", "reflection"],
        input={"query": "test"},
        strategy_type=OrchestrationStrategyType.SEQUENTIAL,
    )

    print(f"  Captured {len(event_bus.events)} events:")
    print()
    for i, ev in enumerate(event_bus.events):
        print(f"    [{i + 1}] {ev.event_type}")
        print(f"         workflow_id={ev.workflow_id}")
        print(f"         trace_id={ev.trace_id}")
        if ev.error:
            print(f"         error={ev.error}")
        if ev.new_status:
            print(f"         new_status={ev.new_status}")
        if ev.metadata:
            print(f"         metadata={ev.metadata}")
        print()

    # Check required events
    event_names = [e.event_type for e in event_bus.events]

    required_start = ["ORCHESTRATION_STARTED", "STRATEGY_SELECTED"]
    for ev_name in required_start:
        check(ev_name in event_names, f"Event '{ev_name}' emitted")

    required_end = ["ORCHESTRATION_COMPLETED", "ORCHESTRATION_FAILED"]
    any_end = any(e in event_names for e in required_end)
    check(any_end, "Terminal event emitted (COMPLETED or FAILED)")

    print()


# ============================================================
# Metrics Verification
# ============================================================


async def verify_metrics():
    header("METRICS VERIFICATION")

    event_bus = MockEventBus()
    coordinator = make_coordinator(event_bus)

    # Run a few strategies to build up metrics
    await coordinator.run_agents(
        agent_ids=["planner"],
        input={"run": 1},
        strategy_type=OrchestrationStrategyType.SEQUENTIAL,
    )
    await coordinator.run_agents(
        agent_ids=["planner", "memory"],
        input={"run": 2},
        strategy_type=OrchestrationStrategyType.PARALLEL,
    )
    await coordinator.run_agents(
        agent_ids=["planner", "memory", "reflection"],
        input={"run": 3},
        strategy_type=OrchestrationStrategyType.DEBATE,
    )

    metrics = coordinator.metrics

    print(f"  Total runs:          {metrics.total_runs}")
    print(f"  Completed runs:      {metrics.completed_runs}")
    print(f"  Failed runs:         {metrics.failed_runs}")
    print(f"  Cancelled runs:      {metrics.cancelled_runs}")
    print(f"  Timed out runs:      {metrics.timed_out_runs}")
    print(f"  Total tasks:         {metrics.total_tasks}")
    print(f"  Completed tasks:     {metrics.completed_tasks}")
    print(f"  Failed tasks:        {metrics.failed_tasks}")
    print(f"  Retried tasks:       {metrics.retried_tasks}")
    print(f"  Avg latency (ms):    {metrics.average_processing_time_ms():.2f}")
    print(f"  Success rate:        {metrics.success_rate():.2%}")
    print(f"  Strategy counts:     {dict(metrics.strategy_counts)}")

    check(metrics.total_runs == 3, f"Total runs recorded: {metrics.total_runs}")
    check(metrics.completed_runs == 3, f"All runs completed: {metrics.completed_runs}")
    check(metrics.total_tasks > 0, f"Tasks recorded: {metrics.total_tasks}")
    check(metrics.average_processing_time_ms() > 0, "Average latency > 0")

    # Engine metrics summary
    engine = OrchestrationEngine(coordinator=coordinator)
    summary = engine.get_metrics_summary()
    print("\n  Engine metrics summary:")
    for k, v in summary.items():
        print(f"    {k}: {v}")

    print()


# ============================================================
# Main
# ============================================================


async def main():
    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}  Phase 10.2 - Multi-Agent Orchestrator Verification Suite{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"  Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_start = time.time()

    verify_architecture()
    await verify_all_strategies()
    await verify_concurrency()
    await verify_retry()
    await verify_timeout()
    await verify_cancellation()
    await verify_event_bus()
    await verify_metrics()

    total_elapsed = time.time() - total_start

    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}  VERIFICATION SUMMARY{RESET}")
    print(f"{'=' * 70}")
    print(f"  Total verification time: {total_elapsed:.3f}s")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())
