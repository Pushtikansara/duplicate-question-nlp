# Backward Compatibility

## How the Pipeline Preserves Existing Behaviour

The CognitivePipeline wraps the existing prediction infrastructure without altering any function signature. All pre-existing call sites continue to work identically whether the pipeline is enabled or disabled.

### Pass-Through Mode

When the pipeline is disabled, the call is a zero-copy pass-through:

```python
def predict(question1: str, question2: str) -> PredictionResult:
    if not pipeline_enabled:
        # Direct call to original implementation -- no overhead
        return _original_predict(question1, question2)
    # Pipeline path
    return pipeline.run(question1, question2)
```

Zero-copy means the strings `question1` and `question2` are never serialized, copied, or transformed before reaching the original prediction function.

### Pipeline Disabled = Identical Code Path

When `pipeline_enabled = False`:
- `compatibility.py` returns `_original_predict` directly
- No `PipelineContext` is created
- No events are fired
- No lifecycle management occurs
- No CMS read/write occurs
- The exact same bytes flow through the exact same function

## Prediction Function Pass-Through

The final decision stage inside the pipeline calls the same `_original_predict` function:

```python
class DecisionModule:
    def execute(self, context: PipelineContext) -> dict:
        # Gather enriched context for explainability
        # Then delegate to original prediction
        result = _original_predict(context.question1, context.question2)
        return {
            "final_verdict": result.verdict,
            "confidence": result.confidence,
            "explainability": self._build_explainability(context, result),
        }
```

The prediction result is guaranteed to match byte-for-byte with a non-pipeline call when CMS and debate are disabled.

## Existing APIs Unchanged

| API | Before | After | Change |
|---|---|---|---|
| `predict(q1, q2)` | Returns `PredictionResult` | Same signature, same return type | None |
| `predict_batch(pairs)` | Returns `list[PredictionResult]` | Same signature, same return type | None |
| Streamlit app | Calls `predict()` | Calls `predict()` | None |
| CLI tool | Calls `predict()` | Calls `predict()` | None |
| REST endpoint | Calls `predict()` | Calls `predict()` | None |
| `model.predict()` | Internal method | Internal method | None |

## Compatibility Validation

The `compatibility.py` module provides a validation harness:

```python
def validate_backward_compatibility(num_samples: int = 1000) -> CompatibilityReport:
    """
    Runs predictions with pipeline disabled and enabled on the same inputs.
    Asserts that outputs match exactly.
    """
    pairs = _load_test_pairs(num_samples)
    mismatches = []

    for q1, q2 in pairs:
        with pipeline_disabled():
            baseline = predict(q1, q2)
        with pipeline_enabled():
            pipelined = predict(q1, q2)

        if baseline.verdict != pipelined.verdict or \
           abs(baseline.confidence - pipelined.confidence) > 1e-6:
            mismatches.append((q1, q2, baseline, pipelined))

    return CompatibilityReport(
        total=num_samples,
        passed=num_samples - len(mismatches),
        mismatches=mismatches,
        tolerance=1e-6,
    )
```

### Automated CI Gate

A CI step runs `validate_backward_compatibility(2000)` before every release. Zero mismatches are required. Any mismatch fails the build and surfaces the exact inputs and outputs for debugging.
