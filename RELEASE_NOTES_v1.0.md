# Release Notes — v1.0.0

*Release Date: 2026-07-27*

---

## Overview

v1.0.0 marks the first stable production release of the Duplicate Question Detection NLP system. The project has evolved from research notebooks through phased development into a production-grade inference system with 11 registered models, a Streamlit dashboard, and a FastAPI multi-agent framework.

---

## What's New

### Production-Ready Models
- **3 Production models** classified and documented: Improved DistilBERT (F1=0.954), DistilBERT Week 3 (F1=0.897), Cross-Encoder-Quora (F1=0.876)
- **3 Research models** maintained for benchmarking: MPNet, E5-quora-finetuned, BGE
- **3 Experimental models** documented with known limitations: E5-base-v2, DeBERTa-v3, Semantic Ensemble
- **2 Legacy models** preserved for reference: TF-IDF approaches

### Threshold Optimization (Phase 11.2)
- Systematic sweep across 101 thresholds per model on 40K validation pairs
- Updated thresholds: Cross-Encoder 0.10→0.52, E5-base-v2 0.35→0.59, E5-quora-finetuned 0.40→0.63
- Validated improvements: Cross-Encoder +0.022 F1, E5-base-v2 +0.146 F1, E5-quora-finetuned +0.034 F1

### Calibration Pipeline
- Three calibration methods: Temperature Scaling, Platt Scaling, Isotonic Regression
- Isotonic selected as best method across all 7 working models
- ECE reduced from 0.09-0.16 to <0.01 for all models

### Repository Cleanup
- Dead configuration removed (~45 unused settings identified and cleaned)
- Backup artifacts removed
- Model registry classified with production tiers
- UI sorts production models first

---

## Breaking Changes

- **Config change**: `BGE-quora-finetuned` removed from `per_model_thresholds` and `sigmoid_params` in `configs/inference.yaml` (model directory does not exist)
- **Config change**: `batch_sizes` section removed from `configs/inference.yaml` (unused — batch sizes are function defaults)
- **Config change**: `app.yaml` no longer contains `default_threshold` or `device` (managed by `inference.yaml`)
- **Model ordering**: UI model selector now sorts by tier (Production → Research → Experimental → Legacy)

---

## Known Limitations

1. **Two duplicate model registries**: `duplicate_question_app._models.registry` and `ares.model_registry` should be consolidated
2. **LR Head duplication**: `all_mpnet_base_v2_lr_head.pkl` is a byte-for-byte copy of `bge_lr_head.pkl`
3. **TF-IDF models broken**: Week 2 models have dimension mismatch (5K vs 10K features)
4. **DeBERTa wrong task**: NLI model used for duplicate detection, severe miscalibration (ECE=0.372)
5. **No id2label in config**: DistilBERT models lack explicit label mapping in config.json
6. **Training config is documentation-only**: Values in `configs/training.yaml` have no runtime effect

---

## Files Changed

- `configs/inference.yaml` — 3 threshold updates, removed dead entries
- `configs/app.yaml` — removed redundant settings
- `configs/evaluation.yaml` — marked as documentation-only
- `configs/training.yaml` — marked as documentation-only
- `configs/paths.yaml` — commented out unused path
- `configs/inference.yaml.bak` — **deleted**
- `src/duplicate_question_app/_models/registry.py` — added `model_tier` field
- `src/ares/model_registry.py` — added `model_tier` field
- `app/components/sidebar.py` — sort by tier, show tier labels
- `README.md` — rewritten for v1.0
- `CHANGELOG.md` — updated with Phase 11.2 and 11.3 entries

---

## New Documents

- `PROJECT_STATUS.md` — project status and metrics
- `MODEL_LIFECYCLE.md` — model lifecycle classification
- `PRODUCTION_MODELS.md` — production model specifications
- `RELEASE_NOTES_v1.0.md` — this file
- `evaluation_results/CLEANUP_REPORT.md` — cleanup recommendations

---

## Download

- Source: [GitHub Repository](https://github.com/your-org/duplicate-question-nlp)
- Docker: See `Dockerfile` and `docker-compose.yml`
- API docs: `http://localhost:8000/docs` (when running ARES API)
