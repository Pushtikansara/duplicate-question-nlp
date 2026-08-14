"""Adaptive Routing Benchmark — Phase 14.

Evaluates the adaptive routing pipeline end-to-end against golden question
pairs and reports difficulty classification, chosen strategy, model
executions, early exit, latency and routing decisions.

Usage:
    python scripts/evaluate_adaptive_routing.py [--warmup] [--verbose]

Without ``--warmup`` models load lazily on first execution, which skews the
first request's latency. With ``--warmup`` every routed model is warmed once
up front (~45s for the default catalog).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ares.adaptive.config_loader import load_adaptive_config
from ares.orchestration.cache import InMemoryCacheProvider
from ares.orchestration.config_loader import (
    build_pipeline_stage_config,
    build_strategy_registry,
)
from ares.orchestration.orchestrator import PredictionOrchestrator
from ares.orchestration.policies import DefaultFallbackPolicy, DefaultRetryPolicy
from ares.orchestration.prediction_service import (
    PredictionService,
    build_default_stage_registry,
)

GOLDEN_CASES: list[dict] = [
    {
        "q1": "what is machine learning",
        "q2": "what is ml",
        "expected": "Duplicate",
        "category": "F",
        "rationale": "acronym-to-expansion synthetic duplicate; abbreviation_relation must escalate",
    },
    {
        "q1": "how does a financial market work",
        "q2": "how does a financial market work",
        "expected": "Duplicate",
        "category": "A",
        "rationale": "exact match -> easy early exit",
    },
    {
        "q1": "what is the capital of france",
        "q2": "what is the largest city in germany",
        "expected": "Non-Duplicate",
        "category": "A",
        "rationale": "easy distinct entities -> cheap early exit",
    },
    {
        "q1": "how to learn python",
        "q2": "how to learn python programming",
        "expected": "Duplicate",
        "category": "A",
        "rationale": "high-overlap duplicate -> cheap early exit",
    },
    {
        "q1": "how much does the iphone cost",
        "q2": "price of iphone 15",
        "expected": "Duplicate",
        "category": "D",
        "rationale": "semantic duplicate with low content overlap",
    },
    {
        "q1": "price of iphone",
        "q2": "cost of samsung galaxy",
        "expected": "Non-Duplicate",
        "category": "E",
        "rationale": "entity-substitution false-positive trap; trust escalation must verify",
    },
    {
        "q1": "what are endothermic reactions",
        "q2": "explain exothermic reactions",
        "expected": "Non-Duplicate",
        "category": "D",
        "rationale": "antonymic prefix pair, distinct content",
    },
    {
        "q1": "i do not want to eat",
        "q2": "i want to eat",
        "expected": "Non-Duplicate",
        "category": "B",
        "rationale": "asymmetric negation -> medium, escalation required",
    },
    {
        "q1": "what is the largest mammal",
        "q2": "what is the smallest ocean",
        "expected": "Non-Duplicate",
        "category": "A",
        "rationale": "easy distinct -> cheap early exit",
    },
    {
        "q1": "what is ai",
        "q2": "what is artificial intelligence",
        "expected": "Duplicate",
        "category": "F",
        "rationale": "acronym-to-expansion synthetic duplicate",
    },
    {
        "q1": "define cnn",
        "q2": "what is a convolutional neural network",
        "expected": "Duplicate",
        "category": "F",
        "rationale": "acronym-to-expansion synthetic duplicate",
    },
    {
        "q1": "how to become a billionaire",
        "q2": "how to become a millionaire",
        "expected": "Non-Duplicate",
        "category": "B",
        "rationale": "near-parallel structure with distinct goal -> medium, escalates",
    },
    {
        "q1": "pancake recipe",
        "q2": "how to make pancakes",
        "expected": "Duplicate",
        "category": "D",
        "rationale": "semantic duplicate with zero content overlap",
    },
]

# NOTE: there is intentionally no default category C (hard/critical) golden:
# with the default text-only difficulty weights the score cannot naturally
# exceed the hard threshold (0.60) -- it requires the cheap-confidence_low,
# long_input or semantic-uncertainty signals that only appear when an upstream
# complexity estimate is available.  Documented in
# docs/architecture/19_PHASE_14_2_ADAPTIVE_INTELLIGENCE.md (STEP 13).


def build_service(warmup: bool) -> PredictionService:
    from ares.adaptive.executor import AdaptivePredictionEngine

    adaptive_config = dict(load_adaptive_config())
    adaptive_config["enabled"] = True

    engine = AdaptivePredictionEngine(config=adaptive_config, warmup=warmup)
    query_pipeline = None
    from ares.query_understanding.query_pipeline import QueryPipeline

    strategy_selector = None
    from ares.orchestration.strategy_registry import StrategySelector

    registry = build_default_stage_registry(
        engine,
        query_pipeline or QueryPipeline(),
        strategy_selector or StrategySelector(build_strategy_registry()),
        cache_provider=InMemoryCacheProvider(512),
        cache_ttl_seconds=300,
        cache_fail_closed=False,
        adaptive_auto_route=True,
        stage_config=build_pipeline_stage_config() or None,
    )

    orchestrator = PredictionOrchestrator(
        registry,
        retry_policy=DefaultRetryPolicy(enabled=False),
        fallback_policy=DefaultFallbackPolicy(enabled=False),
        max_concurrency=4,
        batch_max_pairs=100,
    )
    return PredictionService(orchestrator)


def main() -> int:
    parser = argparse.ArgumentParser(description="Adaptive routing benchmark")
    parser.add_argument("--warmup", action="store_true", help="warm all routed models first")
    parser.add_argument("--verbose", action="store_true", help="print per-case details")
    args = parser.parse_args()

    service = build_service(warmup=args.warmup)

    correct = 0
    rows = []
    for case in GOLDEN_CASES:
        t0 = time.perf_counter()
        result = service.predict(case["q1"], case["q2"])
        latency_ms = (time.perf_counter() - t0) * 1000
        pred = result.prediction
        ok = pred == case["expected"]
        correct += int(ok)

        trace = (result.to_dict().get("orchestration_trace") or {}).get("adaptive_routing") or {}
        difficulty = trace.get("routing", {}).get("difficulty")
        strategy = trace.get("final", {}).get("final_strategy")
        model = (trace.get("final", {}).get("final_model") or "")[:40]
        model_calls = trace.get("execution", {}).get("model_calls")
        early_exit = bool(trace.get("adaptive", {}).get("early_exit"))

        rows.append(
            {
                "case": case["q1"][:32],
                "expected": case["expected"],
                "pred": pred,
                "ok": ok,
                "difficulty": difficulty,
                "strategy": strategy,
                "model": model,
                "calls": model_calls,
                "early_exit": early_exit,
                "latency_ms": round(latency_ms, 1),
            }
        )

    print(f"\nAdaptive routing benchmark — {len(GOLDEN_CASES)} golden cases")
    print(f"Accuracy: {correct}/{len(GOLDEN_CASES)} ({100 * correct / len(GOLDEN_CASES):.0f}%)")
    wrong = [r for r in rows if not r["ok"]]
    if wrong:
        print("Misclassified:")
        for r in wrong:
            print(f"  {r['case']}  expected={r['expected']} got={r['pred']}")
    if args.verbose:
        header = (
            f"{'case':35} {'expected':13} {'pred':13} {'diff':7} {'strat':18} {'calls':5} {'early':6} {'lat(ms)':8}"
        )
        print()
        print(header)
        print("-" * len(header))
        for r in rows:
            print(
                f"{r['case']:35} {r['expected']:13} {r['pred']:13} "
                f"{r['difficulty']:7} {r['strategy']:18} {r['calls']!s:5} "
                f"{str(r['early_exit']):6} {r['latency_ms']:<8}"
            )
    return 0 if correct == len(GOLDEN_CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
