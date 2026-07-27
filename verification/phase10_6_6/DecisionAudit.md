# Decision Audit — Phase 10.6.6

## DecisionAgent — Never Silently Flip Prediction

**File:** `src/ares/agents/decision_agent.py`

### Changes Made
The DecisionAgent now explicitly detects and logs any prediction flips:

1. **Flip Detection Logic** (line ~100):
   - Computes `final_confidence` from raw/adjusted/trust
   - If confidence crosses the 0.5 threshold AND changes from original prediction:
   - Creates a `flip_record` with `before`, `after`, `reason`, `rule`, `confidence_delta`
   - Logs a warning with full details

2. **Flip Record Structure**:
   ```json
   {
     "before": "duplicate",
     "after": "not_duplicate",
     "reason": "confidence_crossed_threshold_due_to_adjustment",
     "rule": "final_confidence >= 0.5 -> duplicate, else not_duplicate",
     "confidence_delta": -0.15
   }
   ```

3. **Evidence Chain**:
   - Every flip is recorded in the `evidence` list
   - Included in the `decision` output as `flip_record` and `prediction_changed`

4. **Display Requirements**:
   - When `prediction_changed` is true, the UI must display:
     - Before prediction
     - After prediction
     - Reason
     - Rule applied
     - Confidence delta

### Confidence Computation
```python
final_confidence = (
    0.3 * raw_confidence +
    0.4 * adjusted_confidence +
    0.3 * trust_score
)
```

### Decision Output Structure
```python
{
    "predicted_label": int,
    "prediction": str,
    "raw_confidence": float,
    "adjusted_confidence": float,
    "trust_score": float,
    "final_confidence": float,
    "final_verdict": str,
    "final_prediction": str,
    "signals": list,
    "conflicts": list,
    "temporal_consistency": dict,
    "model_name": str,
    "flip_record": dict | None,
    "prediction_changed": bool,
    "recommendation": str
}
```

### Silent Flip Prevention
- Before: DecisionAgent could change prediction without recording it
- After: Every prediction change is explicitly detected, logged, and returned
- UI can now display the flip information to the developer
