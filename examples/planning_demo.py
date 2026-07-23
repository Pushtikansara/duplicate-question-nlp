#!/usr/bin/env python3
"""
Planning Engine Demo — Phase 10.5

Shows: Goal → Planner → Plan Graph → Validation → Optimization → Execution → Result
"""

from __future__ import annotations

import asyncio
import time

from ares.planning import (
    PlanningEngine,
    PlanningMetrics,
    PlanningStrategy,
)


def separator(title: str) -> None:
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def print_dict(title: str, data: dict) -> None:
    print(f"\n  {title}:")
    for k, v in data.items():
        if isinstance(v, dict):
            print(f"    {k}:")
            for kk, vv in v.items():
                print(f"      {kk}: {vv}")
        elif isinstance(v, list):
            print(f"    {k}: {v}")
        elif isinstance(v, float):
            print(f"    {k}: {v:.2f}")
        else:
            print(f"    {k}: {v}")


async def main() -> None:
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           PLANNING ENGINE DEMO — PHASE 10.5                        ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    metrics = PlanningMetrics()
    engine = PlanningEngine(metrics=metrics)

    goal_description = "Analyze customer feedback and generate actionable insights report"

    # ---- Step 1: User Goal ----
    separator("1. USER GOAL")
    print(f"\n  Goal: {goal_description}")

    agent_ids = ["agent-analyzer", "agent-extractor", "agent-reporter", "agent-validator"]

    # ---- Step 2: Create Goal ----
    separator("2. GOAL DECOMPOSITION")
    goal = engine.create_goal(goal_description, decompose=True)
    print(f"\n  Goal ID: {goal.goal_id}")
    print(f"  Sub-goals: {len(goal.sub_goals)}")
    for i, sg in enumerate(goal.sub_goals):
        print(f"    {i + 1}. {sg.description} (id={sg.goal_id[:8]})")

    # ---- Step 3: Plan ----
    separator("3. PLANNER")
    start = time.perf_counter()
    graph = engine.create_plan(
        goal,
        strategy=PlanningStrategy.DAG,
        agent_ids=agent_ids,
    )
    plan_time = (time.perf_counter() - start) * 1000
    print(f"\n  Strategy: {graph.plan.strategy.name}")
    print(f"  Plan ID: {graph.plan.plan_id}")
    print(f"  Planning time: {plan_time:.1f}ms")
    print(f"  Nodes: {len(graph.plan.nodes)}")
    print(f"  Edges: {len(graph.plan.edges)}")

    # ---- Step 4: Validation ----
    separator("4. VALIDATION")
    errors = engine.validate_plan(graph, agent_ids)
    if errors:
        print(f"\n  ❌ Validation errors: {len(errors)}")
        for e in errors:
            print(f"    - {e}")
    else:
        print("\n  ✅ Plan validated successfully — no errors")

    # ---- Step 5: Optimization ----
    separator("5. OPTIMIZATION")
    for node in graph.plan.nodes.values():
        node.latency_estimate_ms = 150.0
        node.cost_estimate = 0.5
    stats = engine.optimize_plan(
        graph,
        optimize_latency=True,
        optimize_parallelism=True,
        optimize_cost=True,
        optimize_retries=True,
    )
    before = stats["before"]
    after = stats["after"]
    print(f"\n  Optimizations applied: {', '.join(stats['optimizations_applied'])}")
    print(
        f"  Before — latency: {before['total_latency_estimate_ms']}ms, "
        f"cost: {before['total_cost_estimate']}, "
        f"parallel nodes: {before['parallel_nodes']}"
    )
    print(
        f"  After  — latency: {after['total_latency_estimate_ms']}ms, "
        f"cost: {after['total_cost_estimate']}, "
        f"parallel nodes: {after['parallel_nodes']}"
    )
    impr = stats["improvements"]
    print(
        f"  Improvement — latency: {impr.get('total_latency_estimate_ms_pct', 0):.1f}%, "
        f"parallelism: {impr.get('parallelism_pct', 0):.1f}%"
    )

    # ---- Step 6: Execution Order ----
    separator("6. EXECUTION ORDER")
    order = graph.get_execution_order()
    print()
    for level_idx, level in enumerate(order):
        level_nodes = ", ".join(
            f"{graph.plan.nodes[nid].action} ({nid[:6]})" for nid in level if nid in graph.plan.nodes
        )
        print(f"  Level {level_idx}: [{level_nodes}]")

    # ---- Step 7: Execute ----
    separator("7. EXECUTION")
    result = await engine.execute_plan(graph)
    print(f"\n  Status: {result.status.name}")
    print(f"  Total latency: {result.total_latency_ms:.1f}ms")
    print(f"  Total cost: {result.total_cost}")
    print(f"  Nodes executed: {len(result.node_results)}")
    timeline = result.execution_timeline
    if timeline:
        print()
        for entry in timeline:
            print(f"    [{entry['status']:>10}] {entry['agent_id']:<20} {entry['action']}")

    # ---- Step 8: Full Cycle ----
    separator("8. FULL CYCLE (end-to-end)")
    cycle_result = await engine.full_cycle(
        "Collect data, process it, and generate summary",
        strategy=PlanningStrategy.LINEAR,
        agent_ids=["agent-a", "agent-b", "agent-c"],
        decompose=True,
        validate=True,
        optimize=True,
        execute=True,
    )
    print(f"\n  Total time: {cycle_result['total_time_ms']:.1f}ms")
    print(f"  Validation errors: {len(cycle_result['validation_errors'])}")
    print(f"  Plan status: {cycle_result['plan_result'].status.name if cycle_result['plan_result'] else 'N/A'}")

    # ---- Step 9: Metrics ----
    separator("9. METRICS")
    summary = metrics.summary()
    print_dict("Planning Metrics", summary)

    # ---- Step 10: Plan Graph ----
    separator("10. PLAN GRAPH STRUCTURE")
    graph_dict = graph.to_dict()
    print(f"\n  Plan graph for plan '{graph_dict['plan_id']}':")
    print(f"  Strategy: {graph_dict['strategy']}")
    print(f"  Nodes: {graph_dict['complexity']['nodes']}")
    print(f"  Edges: {graph_dict['complexity']['edges']}")
    print(f"  Levels: {graph_dict['complexity']['levels']}")
    print(f"  Execution order levels: {graph_dict['execution_order']}")

    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           DEMO COMPLETE — PHASE 10.5 SUCCESSFUL                     ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    asyncio.run(main())
