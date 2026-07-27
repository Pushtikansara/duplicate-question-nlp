# Duplicate Question Detection NLP

A production-grade NLP system for detecting duplicate question pairs, with 11 registered models spanning classical ML, transformer fine-tuning, bi-encoders, and cross-encoders. Delivered via a Streamlit dashboard and a FastAPI multi-agent ARES framework.

## Quick Start

```bash
pip install -e ".[dev]"
# Launch the Streamlit dashboard
dqd-app
# Or use the CLI for single predictions
dqd-predict --question1 "How to learn Python?" --question2 "Best way to learn Python"
```

## Production Models

Three models are classified as **Production-ready** (F1 > 0.87):

| Model | F1 | Latency | Use Case |
|-------|-----|---------|----------|
| Improved DistilBERT (Week 4) | 0.954 | 2.7ms | Default — general purpose |
| DistilBERT (Week 3) | 0.897 | 2.6ms | Conservative predictions |
| Cross-Encoder-Quora (Trained) | 0.876 | 2.9ms | Accuracy-critical predictions |

See `PRODUCTION_MODELS.md` for the full model lifecycle and `MODEL_LIFECYCLE.md` for the complete classification.

## Architecture

```
app/                          # Streamlit UI (18 pages)
configs/                      # YAML configuration (8 files)
src/
  duplicate_question_app/     # Core application
    _inference/               # DistilBERT inference pipeline
    _models/                  # Model registry + bi-encoder/cross-encoder loading
    _calibration/             # Platt, Temperature, Isotonic calibration
    _dataset/                 # Data loading + split management
    _evaluation/              # Benchmark suite + metrics
    _config/                  # Configuration loader
  ares/                       # ARES multi-agent inference framework
    api/                      # FastAPI REST API
    inference/                # Inference dispatcher
    model_registry.py         # Duplicate of _models/registry.py
models/                       # Trained model artifacts
tests/                        # 140+ tests (unit, integration, regression, API)
evaluation_results/           # Benchmark outputs + calibration reports
```

## Model Tiers

Models are classified into four lifecycle tiers:

- **Production** (3): Ready for production use, validated on 40K+ pairs
- **Research** (3): Good performance, benchmark-only candidates
- **Experimental** (3): Need further work or retraining
- **Legacy** (2): Broken models kept for reference

## CLI Commands

| Command | Description |
|---------|-------------|
| `dqd` | Diagnostics: health, validate, config, doctor |
| `dqd-app` | Launch Streamlit dashboard |
| `dqd-predict` | Predict from CSV or command-line arguments |
| `dqd-benchmark` | Run full model benchmark (7 models, 5 test sets) |

## API

```bash
# Start the FastAPI ARES API
uvicorn ares.api.main:app

# Predict
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text_a": "How to learn Python?", "text_b": "Best way to learn Python"}'
```

## Requirements

- Python 3.10+
- See `pyproject.toml` for full dependency list
- Optional: CUDA-compatible GPU for faster inference

## Documentation

| Document | Contents |
|----------|----------|
| `RELEASE_NOTES_v1.0.md` | v1.0 release notes |
| `PROJECT_STATUS.md` | Current project status and known issues |
| `MODEL_LIFECYCLE.md` | Full model lifecycle classification |
| `PRODUCTION_MODELS.md` | Production model specifications and recommendations |
| `evaluation_results/CALIBRATION_REPORT.md` | Calibration analysis (Phase 11.2) |
| `evaluation_results/THRESHOLD_ANALYSIS.md` | Threshold optimization report |
| `CHANGELOG.md` | Full change history |

## License

Apache 2.0
