# Startup Validation

## Validation Checks

The following validations run automatically during `initialize_context(validate=True)`:

| # | Check | Error Message |
|---|-------|---------------|
| 1 | `p.project_root.exists()` | `Project root does not exist: {path}` |
| 2 | `p.models_dir.exists()` | `Models directory not found: {path}` |
| 3 | `p.data_dir.exists()` | `Data directory not found: {path}` |
| 4 | `p.week3_model_dir.exists()` | `Week 3 model directory not found: {path}` |
| 5 | `(p.week3_model_dir / "config.json").exists()` | `Week 3 config.json missing: {path}` |
| 6 | `p.week4_model_dir.exists()` | `Week 4 model directory not found: {path}` |
| 7 | `(p.week4_model_dir / "config.json").exists()` | `Week 4 config.json missing: {path}` |

## Error Handling Architecture

Instead of raw Python `AttributeError`:

```
AttributeError: 'NoneType' object has no attribute 'models_dir'
```

The application now uses structured exceptions:

```
app.context.ApplicationBootstrapError
├── ProjectPathsInitializationError
├── ModelRegistryNotLoaded
└── InferenceDispatcherMissing
```

## Startup Report

When validation errors are detected, `render_startup_report(ctx)` displays a structured report inside the Streamlit UI with numbered, descriptive error messages explaining what failed and how to fix it.

## Test Results

| Test | Status |
|------|--------|
| `from app.utils.constants import PATHS` — returns `AppPaths` | ✅ |
| `PATHS is None` after import | ✅ **False** |
| `check_week2_artifacts(PATHS)` — no crash | ✅ |
| `build_registry(PATHS)` — no crash | ✅ |
| `get_model_resolution()` — uses context paths | ✅ |
| All 18 page modules import without `None` | ✅ |
| `ApplicationContext` in session state | ✅ |
| No `AttributeError` during startup | ✅ |
