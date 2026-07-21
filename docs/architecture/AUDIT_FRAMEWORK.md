# Audit Framework -- ARES Phase 8 RTEE

## Overview

Five auditors implement `ABC` interfaces from `interfaces.py` and each produce an `AuditorResult` containing a `score` (0.0 -- 1.0), `details` dict, `warnings` list, and `passed` boolean. All auditors are **read-only**: they inspect, they do not mutate.

## AuditorResult

```python
@dataclass
class AuditorResult:
    module: str
    score: float        # 0.0 - 1.0
    details: dict       # module-specific diagnostics
    warnings: list[str] # human-readable warning messages
    passed: bool        # score >= 0.5
```

---

## 1. RoutingAuditor

**Interface:** `RoutingAuditorABC.audit(routing_result)`

Audits pipeline selection quality.

| Condition | Penalty | Warning |
|---|---|---|
| `routing_result is None` | Score = 0.5 | "No routing result available" |
| `confidence < 0.5` | -0.3 | "Routing confidence low: {c}" |
| Empty `required_modules` | -0.2 | "No required modules specified by routing" |
| Pass threshold | >= 0.5 | -- |

**Score range:** 0.0 -- 1.0 (default 1.0, clamped)

**Details:** `selected_pipeline`, `complexity`, `required_modules`, `skipped_modules`, `routing_confidence`, `pipeline_appropriate`

---

## 2. ReasoningAuditor

**Interface:** `ReasoningAuditorABC.audit(reasoning_result)`

Audits reasoning completeness: premises, hypotheses, evidence, trace, uncertainty.

| Condition | Penalty | Warning |
|---|---|---|
| `reasoning_result is None` | Score = 0.5 | "No reasoning result available" |
| `< 2 premises` | -0.15 | "Low premise count: {n}" |
| `< 1 hypothesis` | -0.15 | "No hypotheses generated" |
| No evidence chains | -0.20 | "No evidence chains found" |
| No reasoning trace | -0.10 | "No reasoning trace available" |
| `uncertainty > 0.8` | -0.20 | "High uncertainty: {u}" |

**Score range:** 0.0 -- 1.0 (default 1.0, clamped)

**Details:** `premise_count`, `hypothesis_count`, `supporting_evidence_count`, `contradicting_evidence_count`, `reasoning_trace_available`, `reasoning_confidence`, `reasoning_uncertainty`

---

## 3. DebateAuditor

**Interface:** `DebateAuditorABC.audit(debate_result)`

Audits multi-agent debate: participation, conflicts, consensus, agreement.

| Condition | Penalty | Warning |
|---|---|---|
| `debate_result is None` | Score = 0.5 | "No debate result available" |
| `< 4 agents` | -0.15 | "Low agent participation: {n}/8" |
| `> 3 conflicts` | -0.15..-0.15 | "High conflict count: {n}" |
| No consensus | -0.30 | "No consensus reached" |
| Consensus confidence < 0.5 | -0.20 | "Low consensus confidence: {c}" |
| Mean agreement < 0.5 | -0.20 | "Low mean agent agreement" |

**Score range:** 0.0 -- 1.0 (default 1.0, clamped)

**Details:** `agent_count`, `vote_count`, `conflict_count`, `consensus_available`, `consensus_confidence`, `mean_agreement`

---

## 4. MemoryAuditor

**Interface:** `MemoryAuditorABC.audit(memory_manager, context)`

Audits memory store health and retrieval quality.

| Condition | Penalty | Warning |
|---|---|---|
| `memory_manager is None` | Score = 0.0 | "No memory manager available" |
| Empty store (total_entries == 0) | -0.30 | "Memory store is empty" |
| `avg_quality < 0.3` | -0.20 | "Low average memory quality: {q}" |
| `avg_confidence < 0.3` | -0.15 | "Low average memory confidence: {c}" |
| Could not access stats | -0.50 | "Could not access memory statistics" |
| No memories retrieved | -0.10 | "No memories retrieved for this prediction" |

**Score range:** 0.0 -- 1.0 (default 1.0, clamped)

**Details:** `total_entries`, `avg_quality`, `avg_confidence`, `memories_retrieved`

---

## 5. ConfidenceAuditor

**Interface:** `ConfidenceAuditorABC.audit(prediction, calibration_data)`

Audits prediction-level confidence and calibration error.

| Condition | Penalty | Warning |
|---|---|---|
| `confidence < 0.6` | -0.30 | "Low confidence: {c}" |
| `|prob_duplicate - 0.5| < 0.1` | -0.20 | "Borderline prediction: prob={p}" |
| `ece > 0.15` (from calibration data) | -0.20 | "High calibration error: ECE={e}" |

**Score range:** 0.0 -- 1.0 (default 1.0, clamped)

**Details:** `confidence`, `prob_duplicate`, `ece` (if calibration provided)
