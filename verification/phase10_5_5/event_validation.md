# Event Validation — Phase 10.5.5

## Lifecycle Events

The demo pipeline emits the following events, each exactly once:

| Order | Event | Source | Description |
|-------|-------|--------|-------------|
| 1 | `demo_started` | demo | Pipeline start with trace_id |
| 2 | `scenario_selected` | demo | Scenario + questions |
| 3 | `planning_started` | demo | Goal description |
| 4 | `planning_completed` | demo | Plan graph validation results |
| 5 | `prediction_started` | demo | Questions being predicted |
| 6 | `prediction_completed` | demo | Prediction result |
| 7 | `semantic_adjustment` | demo | (conditional) When ambiguity detected |
| 8 | `memory_write_started` | demo | Storing prediction |
| 9 | `memory_write_completed` | demo | Memory entry details |
| 10 | `memory_read_started` | demo | Reading stored entries |
| 11 | `memory_read_completed` | demo | Entry count |
| 12 | `reflection_started` | demo | Reflection phase start |
| 13 | `reflection_completed` | demo | Reflection result |
| 14 | `execution_started` | demo | Orchestration phase start |
| 15 | `execution_completed` | demo | Orchestration summary |
| 16 | `demo_completed` | demo | Total time |

## Determinism

- EventBus uses bounded list (max 10000 events)
- Each event has unique event_id (uuid4)
- Events are ordered by emission (append-only)
- `get_events()` returns last N events in order

## No Duplicate Events

Since reflection is disabled in ARES engine (`.with_reflection(False)`) and demo runs reflection explicitly in Phase 5, the `reflection_started`/`reflection_completed` pair is emitted exactly once.
