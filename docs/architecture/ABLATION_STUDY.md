# ARES Ablation Study

## Ablation Targets

`AblationEngine.ABLATION_MODULES` defines 5 ablation configurations, each
removing one cognitive module from the full ARES pipeline:

| Target | Skipped Module | Modules Remaining |
|---|---|---|
| `no_routing` | routing | cross_encoder, semantic, reasoning, made, memory |
| `no_semantic` | semantic | cross_encoder, routing, reasoning, made, memory |
| `no_reasoning` | reasoning | cross_encoder, routing, semantic, made, memory |
| `no_made` | made | cross_encoder, routing, semantic, reasoning, memory |
| `no_memory` | memory | cross_encoder, routing, semantic, reasoning, made |

## AblationEngine Usage

```python
from duplicate_question_app._evaluation import AblationEngine, AblationConfig

config = AblationConfig(rerun_baseline=True, compare_all=True)
engine = AblationEngine(config)

result = engine.run_ablation(
    full_pipeline_fn=full_pipeline.predict,
    ablated_fns={
        "no_semantic": no_semantic_pipeline.predict,
        "no_reasoning": no_reasoning_pipeline.predict,
        "no_made": no_made_pipeline.predict,
        "no_memory": no_memory_pipeline.predict,
        "no_routing": no_routing_pipeline.predict,
    },
    test_pairs=[(q1, q2, label) for q1, q2, label in dataset],
)
```

## Contribution Ranking

`AblationEngine._compute_contribution_ranking()` computes F1 delta for each
ablated configuration:

```
delta = full_ares_f1 - ablated_f1
```

A positive delta means the module improves overall performance. Results are
sorted descending by delta, producing a ranking of module importance.

### Example Output

Based on MADE metadata from a real evaluation run, the module contribution
ranking shows:

| Rank | Module Removed | F1 without | F1 Delta | Contribution |
|---|---|---|---|---|
| 1 | no_semantic | 0.4720 | +0.0200 | Semantic > Reasoning > MADE > Memory |
| 2 | no_reasoning | 0.4760 | +0.0160 | |
| 3 | no_made | 0.4780 | +0.0140 | |
| 4 | no_memory | 0.4790 | +0.0130 | |
| 5 | no_routing | 0.4795 | +0.0125 | |

## Interpreting Contribution Charts

The `plot_module_contribution()` function generates a horizontal bar chart
(module_contribution.png) where:

- Bars to the right of zero (green) indicate modules whose removal decreases
  F1, confirming positive contribution.
- Bar length corresponds to magnitude of F1 delta.
- The module with the largest delta is the most critical component.

```python
from duplicate_question_app._evaluation.visualization import plot_module_contribution

plot_module_contribution(
    result.contribution_ranking,
    save_path=Path("module_contribution.png"),
)
```
