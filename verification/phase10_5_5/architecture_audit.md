# Architecture Audit — Phase 10.5.5

## Pipeline

UI → Session State → Planner → Strategy Resolver → Orchestrator → Predict Agent → Inference Dispatcher → Backend → Memory → Reflection → Response

## Audit Results

### UI → Session State
- Streamlit session state key mismatch fixed: `ares_q1_input` used consistently
- Strategy selectbox correctly maps to PlanningStrategy enums
- Engine initialized once via `_initialized` guard

### Session State → Planner
- Strategy string passed as `strat` to `run_demo()`
- Resolved via `resolve_planning_strategy()` from `ares/orchestration/strategy.py`
- Validation: unknown strategies fall back to LINEAR
- Propagation verified: UI strategy reaches `Planner.plan()` without silent replacement

### Planner → Strategy Resolver
- `resolve_planning_strategy()` converts string to `PlanningStrategy` enum
- Orchestration strategy separate: always SEQUENTIAL (for agent coordination)
- Strategy tracked in result dict: `strategy.requested`, `strategy.resolved`, `strategy.orchestration`

### Orchestrator → Predict Agent
- Agents already executed in phases 1-6 are filtered out
- No duplicate prediction/planning/reflection
- Orchestrator only runs remaining agents

### Predict Agent → Inference Dispatcher
- `ARES.predict()` with `with_reflection(False)` — no internal reflection
- Delegated to `InferenceDispatcher.predict()`
- Post-prediction: semantic validation adjusts confidence for ambiguous entities

### Inference Dispatcher → Backend
- All 5 model types routed correctly: classical-ml, transformer, bi-encoder, cross-encoder, ensemble
- threshold parameter accepted but model-specific threshold from metadata used

### Backend → Memory
- Prediction result stored with tags, agent_id
- Memory capacity limits enforced per tier
- FIFO eviction when capacity exceeded
- TTL sweep available

### Memory → Reflection
- Reflection engine receives adjusted confidence (after semantic validation)
- Consistent mapping: trust⇔risk⇔review⇔recommendations
- All recommendations generated from confidence thresholds (no hardcoded text)

### Reflection → Response
- Result dict includes: plan, prediction, semantic_validation, reflection, memory, calibration, diagnostics

## Issues Found & Fixed
1. **Dual reflection**: ARES internal reflection disabled; demo handles it once
2. **Strategy not tracked**: Added `strategy` block to result dict
3. **Session state key mismatch**: Fixed `ares_q1` vs `ares_q1_input`
4. **DAG over-connection**: Removed all-pairs edges in `_plan_dag`
5. **Recommendations hardcoded**: Now generated dynamically from thresholds
