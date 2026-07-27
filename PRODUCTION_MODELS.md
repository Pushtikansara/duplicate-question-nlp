# Production Models

*Updated: 2026-07-27*

This document specifies the three production-ready models, their configurations, and deployment recommendations.

---

## Default Production Model

**Improved DistilBERT (Week 4)** is the system default.

```
Internal ID:    week4
Architecture:   DistilBERTForSequenceClassification
Parameters:     66.9M
Embedding:      768
Threshold:      0.50 (default — optimal F1 threshold is 0.82, but gain is only +0.002)
Sigmoid:        N/A (transformer — outputs logits directly)
F1 Score:       0.9539
Accuracy:       0.9660
Latency:        2.67ms (CPU)
```

## Production Model Specifications

### 1. Improved DistilBERT (Week 4)

| Attribute | Value |
|-----------|-------|
| **Path** | `models/week4_improved_model/` |
| **Files** | `config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json`, `vocab.txt`, `special_tokens_map.json` |
| **Calibration** | None needed (raw ECE=0.043, isotonic reduces to 0.004) |
| **Deployment** | Always available locally |
| **Recommendation** | Use as default for all predictions |

### 2. DistilBERT (Week 3) — Fallback

| Attribute | Value |
|-----------|-------|
| **Path** | `models/saved_transformer_model/` |
| **Threshold** | 0.50 (default) |
| **F1 Score** | 0.8967 |
| **Latency** | 2.58ms |
| **Use when** | Week 4 is unavailable, or more conservative predictions needed |
| **Note** | Slightly more conservative than Week 4; good second opinion |

### 3. Cross-Encoder-Quora (Trained) — Accuracy Specialist

| Attribute | Value |
|-----------|-------|
| **Path** | `models/cross-encoder-quora/` |
| **Threshold** | 0.52 (updated Phase 11.2, was 0.10) |
| **F1 Score** | 0.8758 |
| **Latency** | 2.86ms |
| **Use when** | Accuracy is critical and latency is acceptable |
| **Strength** | Joint encoding captures full pair context |

---

## Configuration

In `configs/inference.yaml`:

```yaml
default_model: "Improved DistilBERT (Week 4)"
default_device: "cpu"
auto_device: true
max_length: 128
default_threshold: 0.5

per_model_thresholds:
  "Cross-Encoder-Quora (Trained)": 0.52
  "E5-quora-finetuned": 0.63
  "E5-base-v2": 0.59
  "BGE-base-en-v1.5": 0.30
  "MPNet-base-v2": 0.36
```

## Deployment Checklist

- [ ] Model artifacts exist at `models/week4_improved_model/`
- [ ] Model artifacts exist at `models/saved_transformer_model/` (fallback)
- [ ] Model artifacts exist at `models/cross-encoder-quora/`
- [ ] `configs/inference.yaml` has correct thresholds
- [ ] Calibration cache warmed (`evaluation_results/.calibration_cache/`)
- [ ] Tests pass (`pytest tests/regression/`)
- [ ] API endpoints respond within SLA

## Monitoring

- Track F1, Accuracy, and ECE on validation set after each deployment
- Alert if F1 drops > 0.01 from baseline
- Benchmark all 7 working models weekly via `dqd-benchmark`
