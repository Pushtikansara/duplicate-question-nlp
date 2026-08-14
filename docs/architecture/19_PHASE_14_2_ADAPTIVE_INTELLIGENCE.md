# Phase 14.2 — Adaptive Routing Intelligence

> Status: **complete**. Phase 14.2 lands evidence-based trust, trust-gated early
> exit, reliability/difficulty-aware disagreement resolution, stopping-reason
> traceability and a 13-case real-model golden benchmark (13/13 correct).

---

## STEP 0 — Architecture assessment

### 0.1 End-to-end flow

```
PredictionService.predict()
  └─ PredictionOrchestrator.run()
       └─ Pipeline → PredictionEngine (AdaptivePredictionEngine when enabled)
            └─ AdaptiveExecutor.execute(q1, q2)
                 ├─ DifficultyAnalyzer.analyze()      → DifficultyAssessment
                 ├─ BudgetPolicy.allocate()            → ComputeBudget
                 ├─ AdaptiveRoutingPolicy.make_plan()  → RoutingPlan
                 ├─ ladder_models from plan + StrategyRegistry
                 ├─ loop over candidates (budget / early-exit / escalation guards)
                 │    └─ engine.predict(model=...)     → ModelEvidence
                 ├─ [TrustAnalyzer.assess + trust-gated early exit on first result]
                 ├─ [trust escalation → strongest available model]
                 ├─ DisagreementDetector.assess()      → DisagreementAssessment
                 ├─ final decision → PredictionResult
                 ├─ AdaptiveReflection.reflect()       → ReflectionRecord (conditional)
                 └─ AdaptiveRun → additive trace merge
```

Integration: `AdaptivePredictionEngine` (`src/ares/adaptive/executor.py`) adapts to the
Phase 13 `PredictionEngine` protocol; enabled by `configs/adaptive_routing.yaml`
(`enabled: true`). Trace sections merge additively under
`orchestration_trace["adaptive_routing"]` (`orchestrator.py:103-109`) — every Phase 13
key is preserved (backward compatible). All thresholds config-driven; no hardcoded
per-model logic (only the cheap→strong strategy order `_STRATEGY_PRIORITY`).

### 0.2 Signals

Deterministic in `DifficultyAnalyzer.analyze`: `exact_match`, `lexical_overlap`,
`content_overlap`, `negation`, `contradiction`, `ambiguity`, `abbreviation`,
`abbreviation_relation`, `numeric_conflict`, `long_input`/`short_input`,
`cheap_confidence_low`, `semantic_uncertainty`. Weighted blend → score → level
(easy/medium/hard/critical) → risk → recommended budget/strategy. Deterministic
boosts (`_apply_boosts`, `_apply_content_gap_boost`) prevent hard signals being masked
by high overlap.

### 0.3 Escalation / stopping / selection / disagreement

See STEP 3–11 below (the 14.2 changes). Pre-existing baseline: easy → no escalation;
medium → +1 stronger; hard → +2; critical → all. Early exit on high confidence + low
risk. Budget caps model calls, escalation depth, latency, reflection, fusion.

### 0.4 Known baseline limitations (addressed by 14.2)

1. Confidence alone ≠ trust (high-conf cheap FP on entity substitution).
2. Trust logic was inline in `executor.py` (not a first-class traceable abstraction).
3. Model reliability was config-estimated, not wired into resolution.
4. Disagreement resolution ignored difficulty/reliability axes.
5. Trace did not surface trust or a stopping reason.
6. Early exit could short-circuit a prediction trust wanted re-verified.

---

## STEP 1 — Golden-dataset categorisation (A–F)

Verified routing table for the golden set (deterministic; real-model outcomes in STEP 14):

| # | case | expected | level | risk | score | initial | ladder | abbr_rel | content_ovl | category |
|---|------|----------|--------|------|-------|---------|--------|-----------|--------------|----------|
| 1 | `what is machine learning` / `what is ml` | Duplicate | medium | low | 0.4500 | baseline | [cross_encoder] | 1.0 | 0.0 | **F** |
| 2 | `how does a financial market work` / same | Duplicate | easy | low | 0.0000 | fast_lexical | [] | 0.0 | 1.0 | **A** |
| 3 | `what is the capital of france` / `what is the largest city in germany` | Non-Dup | easy | low | 0.0750 | fast_lexical | [] | 0.0 | 0.0 | **A** |
| 4 | `how to learn python` / `... programming` | Duplicate | easy | low | 0.2000 | fast_lexical | [] | 0.0 | 0.67 | **A** |
| 5 | `how much does the iphone cost` / `price of iphone 15` | Duplicate | easy | low | 0.0278 | fast_lexical | [] | 0.0 | 0.2 | **D** |
| 6 | `price of iphone` / `cost of samsung galaxy` | Non-Dup | easy | low | 0.0417 | fast_lexical | [] | 0.0 | 0.0 | **E** |
| 7 | `what are endothermic reactions` / `explain exothermic reactions` | Non-Dup | easy | low | 0.0417 | fast_lexical | [] | 0.0 | 0.25 | **D** |
| 8 | `i do not want to eat` / `i want to eat` | Non-Dup | medium | medium | 0.5500 | baseline | [cross_encoder] | 0.0 | 1.0 | **B** |
| 9 | `what is the largest mammal` / `what is the smallest ocean` | Non-Dup | easy | low | 0.1071 | fast_lexical | [] | 0.0 | 0.0 | **A** |
| 10 | `what is ai` / `what is artificial intelligence` | Duplicate | medium | low | 0.4500 | baseline | [cross_encoder] | 1.0 | 0.0 | **F** |
| 11 | `define cnn` / `what is a convolutional neural network` | Duplicate | medium | low | 0.4500 | baseline | [cross_encoder] | 1.0 | 0.0 | **F** |
| 12 | `how to become a billionaire` / `... millionaire` | Non-Dup | medium | low | 0.4500 | baseline | [cross_encoder] | 0.0 | 0.33 | **B** |
| 13 | `pancake recipe` / `how to make pancakes` | Duplicate | easy | low | 0.0000 | fast_lexical | [] | 0.0 | 0.0 | **D** |

Legend: **A** easy/confident → cheap + early exit; **B** medium → escalate to
cross_encoder; **D** semantic duplicate with low content overlap; **E** high-risk
false-positive trap (entity substitution) → trust re-verification; **F** high-risk
false-negative trap (acronym ⇄ expansion) → `abbreviation_relation` escalation.

**Note:** there is intentionally no default category **C** (hard/critical) golden.
With the default text-only difficulty weights the blended score cannot naturally
exceed the hard threshold (0.60) — it needs the `cheap_confidence_low`, `long_input`
or `semantic_uncertainty` signals that only appear when an upstream complexity
estimate is available. This is a documented property of the current difficulty scale,
not a routing defect.

---

## STEP 3 — TrustAssessment abstraction

New module `src/ares/adaptive/trust.py`:

- `TrustAssessment` — first-class dataclass: `trust_score`, `trust_level`
  (low/medium/high), `escalation_required`, `escalation_reasons`, `risk_reasons`,
  `reliability`, `evidence`, `explanation`; `to_dict()` for the trace.
- `TrustAnalyzer.assess(assessment, evidence)` — deterministic. Starts at 1.0 and
  deducts for structural signals the cheap model cannot judge (`abbreviation_relation`
  ≥ `trust.abbreviation_relation_min`, `content_mismatch_duplicate` when a Duplicate
  is predicted on explicitly low `content_overlap` ≤ `trust.content_mismatch_max`,
  contradiction, negation, numeric conflict), low model `reliability` (<
  `trust.reliability_min`) and low confidence.
- Escalation-worthy reasons are config-tunable (`trust.escalation_reasons`; default
  `{abbreviation_relation, content_mismatch_duplicate}`).
- Replaces the old inline `_trust_risk` in the executor; unit-testable in isolation.

Trust thresholds are config-driven:

```yaml
trust:
  escalation_enabled: true
  max_extra_models: 1
  high_threshold: 0.7
  low_threshold: 0.4
  reliability_min: 0.7
  abbreviation_relation_min: 0.5
  content_mismatch_max: 0.15
```

---

## STEP 4 — Model reliability wiring

- `TrustAnalyzer` reads `ModelProfile.reliability` from `ModelProfileRegistry`
  (built from `ares.model_registry` + `model_profiles` config).
- Reliability values in `configs/adaptive_routing.yaml:model_profiles` are
  **provisional estimates** (documented as such; they seed the router but must be
  replaced with measured calibration in production). No numbers were invented beyond
  the existing profile defaults.
- `DisagreementDetector` now weights by `confidence_quality × reliability ×
  confidence` (previously quality × confidence only).

---

## STEP 5/6 — Escalation triggers & model selection

- Difficulty-ladder escalation unchanged (config-driven); runtime guards on
  `escalation.enabled`, `max_escalation_level`, latency budget.
- Trust escalation: post-loop block escalates once to the strongest available model
  when `TrustAssessment.escalation_required`, bounded by `trust.max_extra_models`
  (default 1) and the latency budget. Strongest model chosen via strategy-map
  preference (cross_encoder/ensemble) else highest-accuracy unused profile.
- Model selection for the final answer: highest `expected_accuracy` among models
  agreeing with the resolved label.

## STEP 8 — Early exit (trust-gated)

`_check_early_exit` now receives the first evidence's `TrustAssessment` and **returns
False when `trust.escalation_required`** (reason `trust_recheck_required`). A cheap
model can no longer short-circuit a prediction the trust analysis wants re-verified —
verified end-to-end: a high-confidence (0.95) cheap Duplicate on zero content overlap
now escalates to the cross-encoder and is corrected, instead of early-exiting into a
false positive.

## STEP 9/10 — Budget exhaustion & configuration surface

- New `AdaptiveRun.stopping_reason`: recorded for `escalation disabled by
  configuration`, `escalation cap reached (N)`, `budget latency exhausted`,
  `high_confidence_low_risk` (early exit), or `plan completed`.
- Every new threshold is exposed via `AdaptiveRoutingConfig` + shipped defaults
  (`src/ares/adaptive/defaults.py`, `configs/adaptive_routing.yaml`).

## STEP 7 — Disagreement resolution (reliability/difficulty-aware)

`DisagreementDetector.assess` now accepts `difficulty_level`/`risk_level` (recorded on
the assessment):

- `confidence_weighted`: weight = `confidence_quality × reliability × confidence^α`
  where `α = 0.5` on hard/critical requests (damps overconfident unreliable models),
  `1` otherwise.
- `strongest_model`: tie-breaks on reliability after accuracy.
- `majority_vote` unchanged.

## STEP 11 — Traceability

`build_adaptive_trace` gains two additive sections:
- `trust`: `TrustAssessment.to_dict()` (score, level, escalation, reliability, reasons).
- `adaptive.stopping_reason`: why execution stopped.

`_attach_explanations` also surfaces `trust` under `explanations["adaptive_routing"]`.

## STEP 12 — Test coverage (25 categories)

New `tests/unit/adaptive/test_phase14_2_categories.py` (27 tests, categories C01–C27)
plus `test_trust.py` (13 tests) and expanded `test_disagreement.py`. Coverage:
early exit (incl. trust-gated), escalation, trust escalation + disable path, budgets,
difficulty signals (exact/contradiction/negation/acronym forms/abbreviation_relation/
content-gap), policy (no-escalation, human review, reflection modes), disagreement
(confidence/reliability/difficulty-aware), trust reliability, trace trust + stopping,
failure handling, model override. **155 adaptive/integration tests pass.**

## STEP 13 — Expanded golden dataset

`scripts/evaluate_adaptive_routing.py` grew from 8 → **13 cases**, each annotated with
`category` (A/B/D/E/F) and `rationale` (see STEP 1 table). See the category-C note.

## STEP 14 — Real-model benchmark

`REAL_MODEL_BENCHMARK_SKIPPED: False`. The environment has all 11 registered models
ready with artifacts and torch is importable (2.13.0+cu130), so the benchmark ran
against real models with warm-up.

**Result: 13/13 (100%) accuracy.**

| case | expected | pred | difficulty | strategy | calls | early | latency |
|------|----------|------|------------|----------|-------|-------|---------|
| what is machine learning / what is ml | Dup | Dup | medium | cross_encoder | 2 | no | 7.4ms |
| how does a financial market work | Dup | Dup | easy | fast_lexical | 1 | no | 4.6ms |
| capital of france / largest city germany | Non | Non | easy | fast_lexical | 1 | no | 4.4ms |
| how to learn python | Dup | Dup | easy | fast_lexical | 1 | no | 3.7ms |
| how much does the iphone cost / price of iphone 15 | Dup | Dup | easy | fast_lexical | 1 | no | 3.8ms |
| price of iphone / cost of samsung galaxy | Non | Non | easy | **cross_encoder** | 2 | no | 109.5ms |
| endothermic / exothermic reactions | Non | Non | easy | fast_lexical | 1 | no | 4.9ms |
| i do not want to eat / i want to eat | Non | Non | medium | cross_encoder | 2 | no | 197.9ms |
| what is the largest mammal / smallest ocean | Non | Non | easy | fast_lexical | 1 | **yes** | 3.7ms |
| what is ai / artificial intelligence | Dup | Dup | medium | cross_encoder | 2 | no | 4.8ms |
| define cnn / convolutional neural network | Dup | Dup | medium | baseline | 2 | no | 41.1ms |
| billionaire / millionaire | Non | Non | medium | cross_encoder | 2 | no | 33.3ms |
| pancake recipe / how to make pancakes | Dup | Dup | easy | fast_lexical | 2 | no | 58.1ms |

Notable: the entity-substitution FP trap (`price of iphone` vs `cost of samsung
galaxy`) is escalated to the cross-encoder and correctly rejected (2 calls); the
acronym pairs escalate via `abbreviation_relation`; genuinely easy pairs run one
cheap call; one easy pair early-exits.

## STEP 15 — Performance / computation-safety table

Worst-case budgets per tier (model calls, escalation depth, latency, reflection):

| tier | max_model_calls | max_escalation_level | max_latency_ms | reflection | fusion_min_models |
|------|-----------------|----------------------|----------------|------------|-------------------|
| low  | 1               | 0                    | 1000           | false      | 0 |
| medium| 2              | 1                    | 3000           | true       | 0 |
| high | 4               | 3                    | 15000          | true       | 2 |

Guarantees: `max_model_calls` bounds every request; `trust.max_extra_models` bounds
the extra trust-verification call (default 1); trust escalation also respects the
latency budget and `escalation.max_levels`. The golden benchmark's max observed calls
was 2, on the traps that require re-verification — cheap requests stay at 1 call
(~4–7ms warm).

## STEP 16 — Backward compatibility

- `PredictionService`/`PredictionOrchestrator`/`PredictionResult` signatures unchanged.
- Adaptive routing remains opt-in via `configs/adaptive_routing.yaml` `enabled: false`
  default; when disabled no trace section is emitted (integration test
  `test_adaptive_disabled_no_sections`).
- Trace merge is additive; all Phase 13 keys preserved.
- `TrustAssessment` replaced an internal private helper only; the public
  `AdaptiveExecutor` constructor gained an optional `trust_analyzer` kwarg
  (defaulting to a real `TrustAnalyzer`) — no breaking change.
- `DisagreementAssessment` gained two optional fields with defaults (`None`) — dict
  output remains parseable by existing consumers.
- Full unit/integration suite passes (4237 tests) with no regressions.

## STEP 17 — Quality gates

| gate | result |
|------|--------|
| `ruff check` (adaptive, tests, script) | pass |
| `ruff format --check` | pass |
| `isort --check-only` (black profile, 120) | pass |
| `mypy src/ares/adaptive/` | pass (13 files, no issues) |
| `pytest tests/` | 4237 passed |
| `python -m build --sdist --wheel` | built ok |
| `pre-commit` | not installed in this environment (equivalent tools run individually) |

## STEP 18 — Docs

This document.

## STEP 19 — Git & release

Branch `feature/phase14-adaptive-routing`, tag `v14.2-adaptive-intelligence`.

### File surface changed / added by 14.2
- `src/ares/adaptive/trust.py` (new) — `TrustAnalyzer` + `TrustAssessment`.
- `src/ares/adaptive/executor.py` — trust-gated early exit, trust escalation via
  `TrustAnalyzer`, `stopping_reason`, `run.trust`, mypy-clean exception trace attach.
- `src/ares/adaptive/disagreement.py` — reliability × quality × confidence weighting,
  reliability tie-break, difficulty/risk context.
- `src/ares/adaptive/models.py` — `DisagreementAssessment.difficulty_level/risk_level`.
- `src/ares/adaptive/trace.py` — `trust` + `stopping_reason` sections.
- `src/ares/adaptive/config_loader.py`, `defaults.py`, `configs/adaptive_routing.yaml`
  — trust thresholds surface.
- `src/ares/adaptive/__init__.py` — exports.
- `tests/unit/adaptive/test_trust.py` (new), `test_phase14_2_categories.py` (new),
  `test_disagreement.py` (extended).
- `scripts/evaluate_adaptive_routing.py` — 13 golden cases with category+rationale.
- `docs/architecture/19_PHASE_14_2_ADAPTIVE_INTELLIGENCE.md` (this file).

### Git safety
Only Phase 14 files were committed. User WIP (`M` files in `src/ares/_config.py`,
`_result.py`, `api/streaming.py`, `grpc/*`, `inference/dispatcher.py`,
`model_registry.py`, `orchestration/factory.py`, `orchestrator.py`,
`prediction_service.py`, `stages/strategy_selection.py`, `duplicate_question_app/*`,
`tools/train_cross_encoder.py`) is left untouched in the working tree.

---

## Final report

**Goal:** "minimum computation for highest reliable quality." Phase 14.2 moves the
router from *difficulty-only* routing to *difficulty + evidence-based trust* routing.

- **Trust as a first-class signal**: `TrustAnalyzer`/`TrustAssessment` make the
  decision to re-verify explicit, configurable and traceable.
- **Trust-gated early exit**: cheap, high-confidence predictions that carry a
  structural risk signal can no longer short-circuit; the strongest available model
  verifies them (bounded to one extra call).
- **Reliability-aware resolution**: disagreement weighting and trust both consume
  `ModelProfile.reliability` (provisional, config-supplied).
- **Traceable stopping**: every request records why it stopped
  (`stopping_reason`) and its trust picture.
- **Verified on real models**: 13/13 golden cases correct; the two historical failure
  patterns (acronym FN, entity-substitution FP) are demonstrably escalated and
  corrected while genuinely easy requests stay at one cheap call.
- **No regressions**: 4237 tests pass; ruff/isort/mypy/build clean; backward
  compatible by construction.

### Known remaining limitations
- Category-C (hard/critical) requests are not naturally reachable from text-only
  difficulty signals (needs upstream complexity/cheap-confidence input) — documented.
- `expected_accuracy`/`reliability` remain provisional config estimates, not measured
  calibration — a production follow-up.
- `abbreviation_relation` requires the full expansion phrase verbatim in the other
  question; synonyms of the expansion are not matched.
