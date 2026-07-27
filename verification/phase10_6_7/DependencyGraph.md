# Application Dependency Graph

```
run_app.py
│
└─► app._entry (main)
    │
    ├─► app.utils.constants
    │   ├── PROJECT_ROOT
    │   ├── PATHS (lazy) ──► duplicate_question_app._config.settings.get_app_paths
    │   ├── _model_cache
    │   └── utility functions
    │
    ├─► app.components.sidebar
    │   ├── app.utils.constants (PATHS, _model_cache)
    │   ├── app.services.runtime (get_model_resolution, get_runtime_context)
    │   │   └── app.context (get_paths)
    │   │   └── duplicate_question_app._config.settings (resolve_model_selection)
    │   │   └── ares.inference.dispatcher
    │   ├── duplicate_question_app._models.registry (build_registry)
    │   └── duplicate_question_app._models.week2 (check_week2_artifacts)
    │
    ├─► app.context
    │   ├── ApplicationContext
    │   ├── initialize_context()
    │   ├── get_paths()
    │   └── startup validation
    │
    ├─► app.pages (18 pages)
    │   └── each page:
    │       ├── app.utils.constants.PATHS  (same cached AppPaths)
    │       ├── app.services.runtime
    │       └── duplicate_question_app._*.py  (semantic, inference, models, etc.)
    │
    └─► app.components.footer
        └─► app.components.helpers
```

## Circular Import Verification

| Path | Result |
|------|--------|
| constants → settings → constants | ✅ No cycle |
| context → settings → context | ✅ No cycle |
| runtime → context → settings → runtime | ✅ No cycle |
| sidebar → constants → sidebar | ✅ No cycle |
| sidebar → runtime → context → sidebar | ✅ No cycle |

## None-Object Verification

| Checkpoint | Verdict |
|------------|---------|
| `constants.PATHS` after import | ✅ `AppPaths` (not `None`) |
| `context.get_paths()` with context set | ✅ `AppPaths` |
| `context.get_paths()` without context | ✅ fallback `get_app_paths()` |
| `runtime.get_model_resolution()` | ✅ uses `get_paths()` |
| `sidebar check_week2_artifacts` | ✅ receives `AppPaths` |
| `build_registry(PATHS)` | ✅ receives `AppPaths` |

## Initialisation Count

| Object | Created | Count |
|--------|---------|-------|
| `AppPaths` in `constants.py` | `__getattr__` first call | 1 |
| `AppPaths` in `_entry.py::main()` | `initialize_context(...)` | 1 (same instance) |
| `AppPaths` in `runtime.py` | removed | 0 |
| `ApplicationContext` in session | `_entry.py::main()` | 1 |
