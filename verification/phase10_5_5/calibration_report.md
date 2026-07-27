# Calibration Report — Phase 10.5.5

## Module

`ares/inference/calibration.py` — post-inference calibration analysis.

## Scoring Pipeline

```
Raw Score
  ↓ _apply_isotonic_scaling()
Calibrated Score
  ↓ compare to threshold
Decision
  ↓
Over/Under-confidence Detection
```

## Model-Specific Scaling

| Model Type | Scaling Function |
|------------|-----------------|
| classical-ml / lr / svm | raw * 0.92 + 0.04 |
| transformer / bert | raw * 0.95 + 0.02 |
| ensemble | raw * 0.97 + 0.01 |
| other | identity (raw) |

## Overconfidence Detection

- Gap between raw and calibrated > 0.15 → overconfident
- Gap between calibrated and raw > 0.15 → underconfident
- Gap ≤ 0.05 → well_calibrated
- Gap ≤ 0.10 → acceptable

## Calibration Report Fields

| Field | Type | Description |
|-------|------|-------------|
| model_name | str | Model identifier |
| raw_score | float | Original model score |
| calibrated_score | float | After scaling |
| threshold | float | Decision threshold |
| decision | str | "duplicate" or "non_duplicate" |
| is_overconfident | bool | Raw over-estimates calibrated |
| is_underconfident | bool | Raw under-estimates calibrated |
| confidence_gap | float | absolute(raw - calibrated) |
| calibration_quality | str | well_calibrated/acceptable/needs_calibration |
