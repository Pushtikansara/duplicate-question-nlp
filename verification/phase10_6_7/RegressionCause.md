# Regression Cause — Phase 10.6

## Root Cause

The `AttributeError: 'NoneType' object has no attribute 'models_dir'` during startup was caused by a single architectural defect:

**`app/utils/constants.py` declared `PATHS = None` as a module-level global, and no code ever assigned a valid `AppPaths` instance to it.**

## How the Defect Manifested

1. `sidebar.py` imports `PATHS` from `app.utils.constants` → gets `None`
2. `sidebar_navigation()` calls `check_week2_artifacts(PATHS)` → passes `None`
3. `check_week2_artifacts(paths)` does `_get_week2_models_dir(paths)` → `paths.models_dir`
4. `None.models_dir` → **`AttributeError`**

## Why It Wasn't Caught

- `build_registry(PATHS)` had a `if paths is None: paths = get_app_paths(...)` fallback, masking the bug there
- `check_week2_artifacts(paths)` had **no** such fallback — it assumed the caller always passed a valid `AppPaths`
- The two functions had inconsistent contracts

## The Wrong Fix (Not Applied)

Adding `if paths is None: paths = get_app_paths()` inside `check_week2_artifacts` would have made the error symptom disappear, but it would **not** have fixed the architectural problem:

- `PATHS` would remain `None` in the module
- Every other consumer that forgot to guard against `None` would hit the same error
- No single initialization point exists

## The Correct Fix (Applied)

1. **`PATHS = None` removed** from `constants.py`
2. **Module `__getattr__` (PEP 562)** returns lazily-initialised `AppPaths` on first access
3. **`ApplicationContext`** created as the canonical holder of shared state
4. **`runtime.py`** no longer creates its own `PATHS` duplicate
5. **Startup validation** catches missing directories before any page renders

## Commit That Introduced the Regression

The `PATHS = None` was almost certainly introduced during an earlier refactoring (Phase 10.6) where a `get_app_paths()` call was removed from the module-level initialisation of `constants.py`, leaving the `None` placeholder without a corresponding assignment point. The diff that caused this would show:

```diff
- PATHS = get_app_paths(PROJECT_ROOT)
+ PATHS = None
```

This change left the module-level variable as a dead `None` that was never re-initialised. The `app/services/runtime.py` file also had its own `PATHS = get_app_paths(...)`, suggesting the initialisation was moved but the old `None` sentinel was left behind.
