# Graph Validation — Phase 10.5.5

## GraphValidator

Created `ares/planning/validator.py` with `GraphValidator` class that checks:

| Check | Method | Description |
|-------|--------|-------------|
| Self-loops | `_check_self_loops` | Detects A→A edges and node.depends_on self-references |
| Duplicate edges | `_check_duplicate_edges` | Detects identical (source, target, condition) tuples |
| Cycles | `_check_cycles` | DFS-based cycle detection (white/gray/black) |
| Missing nodes | `_check_missing_nodes` | Edge source/target not in node set |
| Unreachable nodes | `_check_unreachable_nodes` | BFS from roots, any node not visited is unreachable |
| Execution order | `_check_execution_order` | Topological sort validity |
| Strategy compliance | `_check_strategy_compliance` | LINEAR strategy must have exactly nodes-1 edges |

## DAG Fix (Planner Over-Connection)

**Root Cause**: `_plan_dag` in `planner.py` added all-pairs edges (O(n²)), violating the DAG property.

**Before**: For 6 nodes, added 5 sequential edges + 1 skip + (n-2)+(n-1)+...+1 parallel edges
**After**: Only sequential edges + skip_intermediate edge (n edges total)

## Strategy Compliance

- LINEAR: exact edges = nodes - 1 (linear chain)
- TREE: root + left/right branches + merge node
- DAG: sequential + conditional skip
- HIERARCHICAL: coordinator → sub-coordinator → worker per stage
- REACTIVE: monitor → primary → fallback per stage

## Execution Order

All strategies produce valid topological sorts via `Plan.get_execution_order()`.

## Self-Loop Detection

```python
# Before: not checked
# After: GraphValidator detects self-loops in edges and depends_on
```

## Unreachable Node Detection

BFS from root nodes (nodes with no incoming edges). Any node not reached is reported as unreachable.
