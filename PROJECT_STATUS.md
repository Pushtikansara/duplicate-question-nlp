# Project Status

*Updated: 2026-07-27*

---

## Project Overview

A production-grade duplicate question detection system with 11 registered models, comprehensive evaluation, calibration, and threshold optimization. Ready for v1.0 release.

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Registered models | 11 |
| Working models | 7 |
| Production-ready | 3 |
| Max F1 (single model) | 0.954 (Improved DistilBERT) |
| Avg inference latency | 2.5ms (bi-encoders) — 2.9ms (cross-encoders) |
| Validation pairs | 40,429 |
| Test files | 140+ |
| Configuration files | 8 |
| CLI commands | 5 |
| API endpoints | 25+ |

---

## Model Health Summary

| Status | Count | Models |
|--------|-------|--------|
| ✅ Working | 7 | All except Week 2 models and Ensemble |
| ❌ Broken | 2 | TF-IDF LR + SVM (dimension mismatch) |
| ⚠️ Slow | 1 | Semantic Ensemble (~30s/pair) |
| ⚠️ Wrong task | 1 | DeBERTa-v3 (NLI, not duplicate detection) |

---

## Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Week 1-5 | Foundation: data prep, baselines, transformers, Streamlit app | ✅ |
| Phase 10 | Production stabilization: routing, ARES, benchmarks | ✅ |
| Phase 11.0 | Model truth audit | ✅ |
| Phase 11.1 | Model benchmarking (7 models, 40K pairs) | ✅ |
| Phase 11.2 | Threshold optimization + calibration | ✅ |
| Phase 11.3 | **Production cleanup + v1.0 release** | ✅ |

---

## Known Issues

1. **Duplicate registries**: `_models/registry.py` and `ares/model_registry.py` are nearly identical copies — consolidation deferred
2. **LR head copy**: MPNet LR head file is a binary copy of BGE's (same MD5 hash)
3. **Missing id2label**: DistilBERT model configs lack `id2label` mapping
4. **Training config is doc-only**: `configs/training.yaml` values have no runtime effect
5. **TF-IDF models broken**: Not fixable without retraining with consistent vectorizer
6. **Placeholder URLs**: `pyproject.toml` still references `your-org` GitHub URLs

---

## Next Steps

Post-v1.0 work items (not blocking release):

1. Consolidate duplicate model registries
2. Fix LR head file duplication
3. Retrain E5-base-v2 with proper threshold
4. Add id2label to model configs
5. Make training config functional
6. Update placeholder URLs in pyproject.toml
