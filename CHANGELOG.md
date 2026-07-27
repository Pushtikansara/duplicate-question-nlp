# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-27

### Added

- **Model Lifecycle Classification (Phase 11.3)**: All 11 models classified into Production (3), Research (3), Experimental (3), and Legacy (2) tiers with `model_tier` field in both `_models/registry.py` and `ares/model_registry.py`.
- **Release Documentation**: `RELEASE_NOTES_v1.0.md`, `PROJECT_STATUS.md`, `MODEL_LIFECYCLE.md`, `PRODUCTION_MODELS.md` generated.
- **Repository Cleanup Report**: `evaluation_results/CLEANUP_REPORT.md` identifying ~200MB of cleanup candidates.

### Changed

- **UI Model Selector**: Sidebar now sorts models by tier (Production → Research → Experimental → Legacy) with visual tier labels.
- **README.md**: Rewritten for v1.0 to reflect current project state with all 11 models, CLI commands, and API documentation.
- **Configuration Cleanup**:
  - Removed `default_threshold` and `device` from `configs/app.yaml` (redundant — managed by `inference.yaml`)
  - Removed `BGE-quora-finetuned` from `configs/inference.yaml` (phantom model — directory does not exist)
  - Removed unused `batch_sizes` section from `configs/inference.yaml`
  - Removed `baseline_models` from `configs/evaluation.yaml`
  - Commented out unused `finetuned_bge_dir` in `configs/paths.yaml`
  - Marked `configs/training.yaml` and `configs/evaluation.yaml` as documentation-only
  - Deleted `configs/inference.yaml.bak` (stale backup from Phase 11.2)

### Removed

- `configs/inference.yaml.bak` — stale threshold backup (0.10/0.35/0.40)

## [0.3.0] - 2026-07-27

### Changed

- **Threshold Optimization (Phase 11.2)**: Updated 3 decision thresholds in `configs/inference.yaml` based on systematic threshold sweep analysis on the validation set (40,429 pairs, 101 thresholds per model):
  - `Cross-Encoder-Quora (Trained)`: 0.10 → 0.52 (F1: 0.8536 → 0.8758, +0.022)
  - `E5-base-v2`: 0.35 → 0.59 (F1: 0.5611 → 0.7068, +0.146)
  - `E5-quora-finetuned`: 0.40 → 0.63 (F1: 0.7323 → 0.7667, +0.034)
  - All other per-model thresholds (BGE-base-en-v1.5: 0.30, MPNet-base-v2: 0.36, BGE-quora-finetuned: 0.38) and default threshold (0.50) remain unchanged.

### Added

- **Calibration Analysis Report**: `evaluation_results/CALIBRATION_REPORT.md` with per-model calibration method comparison (Temperature, Platt scaling, Isotonic) on 2,000-pair stratified validation subset.
- **Threshold Analysis Report**: `evaluation_results/THRESHOLD_ANALYSIS.md` with per-model optimal thresholds for F1, Accuracy, MCC, Balanced Accuracy, and Cost.
- **Visualizations**: 21 PNG plots across `evaluation_results/RELIABILITY_DIAGRAMS/`, `THRESHOLD_SWEEP/`, and `PROBABILITY_DISTRIBUTIONS/`.
- **Machine-readable summary**: `evaluation_results/MODEL_CALIBRATION_TABLE.csv`.

### Fixed

- **E5-base-v2 model resolution**: `_predict_bi_encoder` in `phase11_2_calibration_analysis.py` bypasses `resolve_best_available_e5_model()` to prevent auto-upgrading E5-base-v2 to E5-quora-finetuned, preserving separate evaluation of both models.
- **DistilBERT model versioning**: `load_model_and_tokenizer` receives correct `model_version` parameter to distinguish Week 3 vs Week 4 DistilBERT checkpoints.

## [0.2.0] - 2026-07-19

### Added

- Phase 5: Professional packaging and developer tooling
  - `pyproject.toml` with full project metadata
  - CLI entry points: `dqd`, `dqd-app`, `dqd-predict`, `dqd-benchmark`
  - Split requirements: `requirements-dev.txt`, `requirements-test.txt`, `requirements-docs.txt`
  - `.pre-commit-config.yaml` with 10 professional hooks
  - `.editorconfig` for cross-editor consistency
  - `LICENSE` (Apache 2.0)
  - `CHANGELOG.md` (this file)
  - `CONTRIBUTING.md` with development workflow guide
  - `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)
  - `MANIFEST.in` for sdist packaging
  - `__version__` attribute and version tracking
  - Code quality tooling: Black, Ruff, isort, mypy

- Phase 4: Configuration, logging, and error handling
  - 8 YAML configuration files under `configs/`
  - Centralized configuration loader with `DQD_*` environment overrides
  - Structured logging system (console + rotating file handlers)
  - Exception hierarchy with 10 standardized exception types
  - `.env.example` for local development
  - Print-to-logging migration in `src/duplicate_question_app/`

## [0.1.0] - 2026-07-19

### Added

- Phase 3: Layered architecture with 15 subpackages
- Phase 2: Modular Streamlit dashboard (5 packages, 41 files)
- Phase 1: Baseline research project with notebooks and monolithic app

v0.9.3

Added Enterprise Plugin System

Plugin Lifecycle

Plugin Discovery

Plugin Registry

Dependency Resolution

Plugin Configuration

77 Tests

Zero Ruff Violations
