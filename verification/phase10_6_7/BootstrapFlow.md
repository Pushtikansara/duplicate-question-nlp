# Bootstrap Flow

## Startup Sequence

```
run_app.py
│
└─► from app._entry import main
    │
    ├─► Module-level (import time):
    │   ├─ _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    │   ├─ _SRC_DIR = _PROJECT_ROOT / "src"
    │   ├─ sys.path inserts
    │   ├─ import streamlit as st
    │   ├─ from app.components.sidebar import sidebar_navigation
    │   │   └─ from app.utils.constants import PATHS
    │   │       └─ constants.__getattr__("PATHS")  ← lazy init
    │   │           └─ get_app_paths(PROJECT_ROOT)  ← **EXACTLY ONCE**
    │   │       └─ PATHS = AppPaths(...)
    │   └─ from app.pages import (...)
    │       └─ each page: from app.utils.constants import PATHS
    │           └─ returns cached _PATHS  ← same object
    │
    └─► main() (runtime):
        ├─ 1. initialize_context(paths=get_app_paths(_BOOT_ROOT))
        │   ├─ ApplicationContext(paths=...)
        │   ├─ _run_startup_validation(ctx)
        │   ├─ set_context(ctx)
        │   └─ st.session_state["app_context"] = ctx
        │
        ├─ 2. _init_session_state()
        │
        ├─ 3. _sync_model_from_query()
        │
        ├─ 4. sidebar_navigation()
        │   ├─ from app.context import get_paths
        │   ├─ registry = build_registry(get_paths())  ← session state context
        │   ├─ check_week2_artifacts(get_paths())      ← valid AppPaths
        │   └─ get_model_resolution()                  ← uses context paths
        │
        └─ 5. _safe_render(render_fn, page_name)
            └─ page.render()
                └─ from app.utils.constants import PATHS
                   └─ returns cached _PATHS (same object as context)
```

## Argument Flow

| Step | Component | Argument | Source |
|------|-----------|----------|--------|
| 1 | `initialize_context` | `paths: AppPaths` | `get_app_paths(PROJECT_ROOT)` |
| 2 | `sidebar_navigation` | (none) | Reads `st.session_state["app_context"]` |
| 3 | `build_registry` | `paths` | `get_paths()` → context.paths |
| 4 | `check_week2_artifacts` | `paths` | `get_paths()` → context.paths |
| 5 | `resolve_model_selection` | `paths` | `get_paths()` → context.paths |
| 6 | Pages | `PATHS` import | `constants.__getattr__` → same AppPaths |

## Key Properties

- **PATHS is created exactly once**: in `constants.__getattr__` (lazy, at first import)
- **ApplicationContext is initialized exactly once**: in `_entry.py::main()`, guarded by `if "app_context" not in st.session_state`
- **Every consumer receives the same paths object**: the `AppPaths` frozen dataclass is immutable and shared by reference
- **No module-level imports of `None`**: the `__getattr__` mechanism guarantees PATHS is always an `AppPaths` when accessed
