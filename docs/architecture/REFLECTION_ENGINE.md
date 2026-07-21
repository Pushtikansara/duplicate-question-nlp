# Reflection Engine -- ARES Phase 8 RTEE

## Overview

`ReflectionEngine` is the central orchestrator of the Reflection, Trust & Explainability Engine (RTEE). It coordinates 16 injected dependencies across audit, trust, explainability, consistency, evidence, quality, recommendation, and human-review subsystems to produce a `ReflectionResult` for every inference.

## Constructor -- Dependency Injection

All 12+ components are injected via `__init__` with lazy defaults:

```python
ReflectionEngine(
    config: ReflectionConfig | None = None,
    trust_engine: TrustEngine | None = None,
    routing_auditor: RoutingAuditor | None = None,
    reasoning_auditor: ReasoningAuditor | None = None,
    debate_auditor: DebateAuditor | None = None,
    memory_auditor: MemoryAuditor | None = None,
    confidence_auditor: ConfidenceAuditor | None = None,
    explainability_engine: ExplainabilityEngine | None = None,
    consistency_checker: ConsistencyChecker | None = None,
    evidence_analyzer: EvidenceAnalyzer | None = None,
    recommendation_engine: RecommendationEngine | None = None,
    human_review_decider: HumanReviewDecider | None = None,
    quality_estimator: QualityEstimator | None = None,
    plugins: list[ReflectionPlugin] | None = None,
)
```

Each optional parameter defaults to a fresh instance when `None`, making the engine usable out-of-the-box while remaining fully configurable for testing and customisation.

## `reflect()` Method

Signature:

```python
def reflect(
    self,
    prediction: dict[str, Any],
    routing_result: Any = None,
    reasoning_result: Any = None,
    debate_result: Any = None,
    memory_manager: Any = None,
    pipeline_context: Any = None,
    calibration_data: dict[str, Any] | None = None,
) -> ReflectionResult
```

### Execution Pipeline

1. **Plugin before hook** -- Iterates `self.plugins`, calling `before_reflection(pipeline_context)` on each.
2. **Audit phase** -- Runs each enabled auditor, catching and logging exceptions per-auditor:
   - `RoutingAuditor.audit(routing_result)`
   - `ReasoningAuditor.audit(reasoning_result)`
   - `DebateAuditor.audit(debate_result)`
   - `MemoryAuditor.audit(memory_manager, pipeline_context)`
   - `ConfidenceAuditor.audit(prediction, calibration_data)`
3. **Evidence analysis** -- `EvidenceAnalyzer.analyze(reasoning_result, debate_result)` extracts total evidence, supporting/contradicting counts, type distribution, and completeness.
4. **Explainability** -- `ExplainabilityEngine.generate()` produces human-readable, technical, and module-contribution explanations.
5. **Consistency check** -- `ConsistencyChecker.check()` returns a list of `ConsistencyWarning` covering reasoning conflicts, debate inconsistency, and cross-module disagreement.
6. **Trust computation** -- `TrustEngine.compute_trust_score()` returns the weighted composite score, `TrustLevel`, and `RiskLevel`.
7. **Recommendations** -- `RecommendationEngine.generate()` produces applicable `RecommendationType` values.
8. **Human review decision** -- `HumanReviewDecider.should_review()` returns `(bool, reason)`.
9. **Quality estimation** -- `QualityEstimator.estimate()` returns metadata about overall quality.
10. **Result assembly** -- All assessments, scores, warnings, recommendations, and metadata are packed into a `ReflectionResult`.
11. **Plugin after hook** -- Calls `after_reflection(result)` on each plugin.

## Plugin System

Plugins implement `ReflectionPlugin` (from `interfaces.py`):

```python
class ReflectionPlugin(ABC):
    def before_reflection(self, context: Any) -> Any: ...
    def after_reflection(self, result: Any) -> Any: ...
    def name(self) -> str: ...
```

Built-in: `DefaultReflectionPlugin` (no-op passthrough). Custom plugins can be injected at construction for logging, telemetry, metric emission, or side-effect orchestration.

## Configuration (`ReflectionConfig`)

| Parameter | Default | Purpose |
|---|---|---|
| `enable_routing_audit` | True | Enable/disable routing auditor |
| `enable_reasoning_audit` | True | Enable/disable reasoning auditor |
| `enable_debate_audit` | True | Enable/disable debate auditor |
| `enable_memory_audit` | True | Enable/disable memory auditor |
| `enable_confidence_audit` | True | Enable/disable confidence auditor |
| `enable_explainability` | True | Enable/disable explainability generation |
| `enable_consistency_check` | True | Enable/disable consistency checks |
| `enable_recommendations` | True | Enable/disable recommendation engine |
| `enable_human_review` | True | Enable/disable human review decider |

## Result (`ReflectionResult`)

A frozen-style dataclass (mutable by convention) holding every output artifact. Key fields: `trust_score`, `trust_level`, `risk_level`, individual auditor assessments, `explainability_score`, `evidence_completeness`, `consistency_warnings`, `recommendations`, `human_review_required`, `human_review_reason`, `metadata`, and `timestamp`. Serializable via `to_dict()`.

## Error Isolation

Each subsystem call is wrapped in `try/except` with `logger.warning`. Failure in one auditor does not block downstream phases; missing assessments contribute default values or reduced scores.
