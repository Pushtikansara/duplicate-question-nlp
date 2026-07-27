# Repository Cleanup Report

*Generated: 2026-07-27*

This report identifies files and directories that are candidates for removal or archiving. No files were deleted. Each item includes the rationale and recommended action.

---

## 1. Stray Artifacts (Root Level)

| File | Size | Reason | Action |
|------|------|--------|--------|
| `=0.23.0` | ~1B | Stray file from pip/pipenv redirect | Delete |
| `phase11_eval_output.log` | ~50KB | Leftover from Phase 11 evaluation run | Delete or move to logs/ |

## 2. Build & Distribution Artifacts

| Path | Reason | Action |
|------|--------|--------|
| `build/` | Package build output (2K+ pyc duplicates of source) | Add to `.gitignore`, delete |
| `dist/` | Distribution packages (`.tar.gz`, `.whl`) | Add to `.gitignore`, delete |
| `src/duplicate_question_detection.egg-info/` | Egg metadata from development install | Add to `.gitignore`, delete |

## 3. Cache Directories (Regenerable)

| Path | Reason | Action |
|------|--------|--------|
| 90+ `__pycache__/` directories (745 .pyc files) | Python bytecode cache | Add `__pycache__/` to `.gitignore`, clean |
| `.pytest_cache/` | Test runner cache | Add to `.gitignore`, delete |
| `.mypy_cache/` | Type checking cache | Add to `.gitignore`, delete |
| `.ruff_cache/` | Linter cache | Add to `.gitignore`, delete |
| `htmlcov/` | Coverage HTML reports | Add to `.gitignore`, delete |

## 4. Runtime Memory State

| Path | Reason | Action |
|------|--------|--------|
| `.ares_memory/` | Runtime agent memory (working/, short_term/, long_term/ JSON files) | Add to `.gitignore`, delete (regenerable) |

## 5. Virtual Environment

| Path | Reason | Action |
|------|--------|--------|
| `test-sdk/` | Full Python venv committed to repo | Add to `.gitignore`, delete |

## 6. Obsolete Configuration

| Path | Reason | Action |
|------|--------|--------|
| `configs/inference.yaml.bak` | **ALREADY DELETED** | Was a backup of pre-11.2 thresholds |
| `.ares.toml` | Empty config file (single comment line) | Delete or populate |

## 7. Historical Phase Documentation

| Path | Reason | Action |
|------|--------|--------|
| `PHASE4_COMPLETION.md` | Historical phase completion doc | Archive or delete |
| `PHASE6_COMPLETION.md` | Historical phase completion doc | Archive or delete |
| `PHASE7_5_COMPLETION.md` | Historical phase completion doc | Archive or delete |
| `PHASE7A_COMPLETION.md` | Historical phase completion doc | Archive or delete |
| `PHASE8_COMPLETION.md` | Historical phase completion doc | Archive or delete |
| `QUALITY_REPORT.md` | Historical quality report | Archive or delete |
| `MODEL_TRUTH_AUDIT.md` | Phase 11.0 investigation report | Archive or delete |
| `TEST_INFRASTRUCTURE_FIX.md` | Infrastructure fix note | Archive or delete |

## 8. Empty or Near-Empty Directories

| Path | Reason | Action |
|------|--------|--------|
| `docs/ADR/` | Empty directory (0 files) | Delete (no ADRs ever created) |
| `assets/` | Contains only `.gitkeep` | Remove `.gitkeep`, delete if unused |
| `evaluation_results/PR_CURVES/` | Contains only `README.md` (no images) | Remove directory |
| `evaluation_results/ROC_CURVES/` | Contains only `README.md` (no images) | Remove directory |

## 9. Intermediate Training Checkpoints

| Path | Reason | Action |
|------|--------|--------|
| `models/transformer_training_outputs/` | 3 checkpoint dirs (~1.5GB) from Week 3 training | Archive to external storage, delete from repo |

## 10. Orphaned Source File

| Path | Reason | Action |
|------|--------|--------|
| `src/duplicate_question_app/inference.py` | Empty 0-byte file | Delete |

## 11. Documentation that May Be Stale

| Path | Reason | Action |
|------|--------|--------|
| `docs/` (~100+ files) | Contains phase10 docs, weekly reports, research papers | Audit for staleness; some may be outdated |

---

## Summary

| Category | Items | Total Estimated Size |
|----------|-------|---------------------|
| Delete immediately | ~12 | < 100KB |
| Add to .gitignore + delete | ~5 directories | ~100MB+ (mostly pycache) |
| Archive or delete | ~10 | < 5MB |
| Review separately | docs/ tree | ~50MB |

Total cleanup potential: **~200MB+** of artifacts, caches, and stale files.
