# Initialisation Audit

## Before Phase 10.6.7

| Location | File | Status | Problem |
|----------|------|--------|---------|
| `PATHS = None` | `app/utils/constants.py:84` | ❌ GLOBAL | Never re-assigned; all consumers get `None` |
| `PATHS = get_app_paths(...)` | `app/services/runtime.py:22` | ❌ DUPLICATE | Creates separate instance; used only in one function |
| `PATHS = None` | `src/.../_models/embeddings.py:26` | ⚠️ LAZY | Uses `get_paths()` pattern; works but duplicates |
| `get_app_paths()` calls | 49 locations | ❌ FRAGMENTED | Each call creates new `AppPaths`; no single source |

## After Phase 10.6.7

| Location | File | Status | Mechanism |
|----------|------|--------|-----------|
| `_PATHS = get_app_paths()` | `app/utils/constants.py:100` | ✅ SINGLE | Module `__getattr__` caches on first access |
| `ApplicationContext.paths` | `app/context.py:38` | ✅ AUTHORITY | Session state holds the canonical reference |
| `get_paths()` | `app/context.py:72` | ✅ ACCESSOR | All consumers go through this |
| `get_app_paths()` calls | unchanged | ✅ TOLERATED | CLI/tools still create their own (acceptable for scripts) |

## What Changed

1. **Removed** `PATHS = None` from `constants.py`
2. **Added** `constants.__getattr__` (PEP 562) — returns lazily-cached `_PATHS`
3. **Added** `app/context.py` — `ApplicationContext`, `initialize_context()`, `get_paths()`
4. **Removed** `PATHS = get_app_paths(...)` from `app/services/runtime.py`
5. **Changed** `runtime.get_model_resolution()` to use `get_paths()` from context
6. **Added** startup validation in `_entry.py::main()` with structured error reporting

## Global State Elimination

| Variable | Before | After |
|----------|--------|-------|
| `constants.PATHS` | `None` (dead) | Lazy `AppPaths` via `__getattr__` |
| `runtime.PATHS` | `AppPaths` (live, duplicate) | Removed |
| `embeddings.PATHS` | `None` (lazy) | Unchanged (its own `get_paths()` — acceptable for module scope) |
| `st.session_state["app_context"]` | (did not exist) | Single `ApplicationContext` |
