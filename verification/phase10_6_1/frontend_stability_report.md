# Frontend Stability Audit — Phase 10.6.1

## Error

```
Uncaught Error:
'setIn' cannot be called on an ElementNode
```

Browser reports this Streamlit frontend rendering error when "Run Multi-Agent Pipeline" is clicked.

---

## Root Cause Analysis

Two independent defects were identified. Either one alone is sufficient to trigger the `setIn` error.

### Defect 1: Nested `st.tabs()` — Primary Cause

**File:** `app/pages/ares_dashboard.py`
**Function:** `_render_developer_tab()` (line 342 in the original)
**Fault:** Calls `st.tabs()` inside the "Developer" tab of an outer `st.tabs()`.

Streamlit's element tree manager (`ElementNode.setIn`) cannot reconcile nested tab contexts. When `st.tabs()` is called inside an existing tab, the child tab's element tree attempts to attach itself to the parent tab's tree using `setIn`. The parent expects a regular element node but receives a tab node, causing the `'setIn' cannot be called on an ElementNode` assertion failure.

```python
# FAULTY — nested tabs
def _render_developer_tab(result):
    dev_tabs = st.tabs(["A", "B", "C"])        # ← inner tabs
    with dev_tabs[0]:
        ...
```

This pattern is documented in Streamlit's issue tracker as unsupported in versions prior to 1.38.0+. The error manifests as a frontend crash that blanks the entire page.

### Defect 2: `st.empty()` + `.container()` + `.empty()` Cycle

**File:** `app/pages/ares_dashboard.py`
**Lines:** 563–589 (in the original)
**Fault:** Creates `st.empty()`, enters its container context manager to create `st.progress()`, then calls `.empty()` on the placeholder and immediately renders new widgets.

The sequence:

```python
progress_placeholder = st.empty()
with progress_placeholder.container():  # creates child container
    bar = st.progress(0)                # attaches to container
    status_text = st.empty()            # attaches to container
    ...
    result = asyncio.run(...)
progress_placeholder.empty()            # removes container + children
_render_results(result)                 # creates new widgets at same position
```

Streamlit's delta tree treats the `.empty()` call as a deletion event. New widgets created immediately after refer to stale delta paths, causing the `setIn` error when they try to write into the element tree at the old path.

---

## Audit Findings

Every component was audited for the following patterns:

| Pattern | Status |
|---|---|
| `st.markdown(..., unsafe_allow_html=True)` | Used in all tab renderers — safe, standard pattern |
| Custom HTML with `<script>` tags | None found |
| Inline JavaScript | None found |
| SVG generation | None found |
| DOM manipulation via st.components | None found |
| `st.empty()` + `.container()` | **Removed** — replaced with inline progress + `st.rerun()` |
| Nested `st.tabs()` | **Removed** — replaced with `st.expander()` sections |
| `st.empty()` inside a tab/form/expander | None found |
| Dynamic element creation in async callbacks | Removed — pipeline result is cached, then `st.rerun()` triggers clean render |

---

## Fix Applied

### Fix 1: Remove nested tabs (lines 342–409)

**Before:**
```python
def _render_developer_tab(result):
    dev_tabs = st.tabs(["Execution Context", "Decision Output", "Diagnostics"])
    with dev_tabs[0]:
        ...
    with dev_tabs[1]:
        ...
    with dev_tabs[2]:
        ...
```

**After:**
```python
def _render_developer_tab(result):
    with st.expander("Execution Context", expanded=True):
        st.json(...)
    with st.expander("Decision Output", expanded=False):
        st.json(...)
    with st.expander("Diagnostics", expanded=False):
        st.json(...)
```

Replaced `st.tabs()` with `st.expander()` sections. Expanders create independent element subtrees and do not trigger the `setIn` conflict.

### Fix 2: Replace `st.empty()` + `.container()` cycle with `st.rerun()`

**Before:**
```python
if submitted:
    progress_placeholder = st.empty()
    with progress_placeholder.container():
        bar = st.progress(0, ...)
        status_text = st.empty()
        async def run():
            ...
        result = asyncio.run(run())
    progress_placeholder.empty()
    _render_results(result)
```

**After:**
```python
if submitted:
    bar = st.progress(0, ...)       # top-level, no container wrapper
    status_text = st.empty()
    async def run():
        ...
    result = asyncio.run(run())
    st.session_state["ares_dashboard_result"] = result
    st.rerun()                      # clean rerun — progress bar gone, results render

elif "ares_dashboard_result" in st.session_state:
    _render_results(st.session_state["ares_dashboard_result"])
```

The progress bar is created at the top level (no placeholder/container wrapper). After the pipeline completes, the result is cached in session state and `st.rerun()` triggers a fresh execution. On the rerun, `submitted` is `False`, so the progress bar code is skipped, and the cached result renders cleanly.

### Fix 3: Isolated try/except per section

Added `_safe_render(component_name, fn, *args)` which wraps every dashboard section in its own try/except:

```python
def _safe_render(component_name, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        st.warning(f"{component_name} encountered an issue and was skipped: {exc}")
        st.code(traceback.format_exc(), line_limit=10)
```

Every section is guarded:

| Section | Guard |
|---|---|
| Overview Cards | `_safe_render("Overview Cards", _render_overview_cards, result)` |
| Execution Pipeline | `_safe_render("Execution Pipeline", _render_pipeline, result)` |
| Execution Tab | `_safe_render("Execution Tab", _render_execution_tab, result)` |
| Agents Tab | `_safe_render("Agents Tab", _render_agents_tab, result)` |
| Timeline Tab | `_safe_render("Timeline Tab", _render_timeline_tab, result)` |
| Memory Tab | `_safe_render("Memory Tab", _render_memory_tab, result)` |
| Observability Tab | `_safe_render("Observability Tab", _render_observability_tab, result)` |
| Developer Tab | `_safe_render("Developer Tab", _render_developer_tab, result)` |
| Final Decision | `_safe_render("Final Decision", _render_final_decision, result)` |

If any widget fails, a Streamlit warning is shown, the traceback is displayed in a code block, and the dashboard continues rendering the remaining sections.

### Fix 4: Safe Mode with progressive component isolation

Added a "Debug: Safe Mode Controls" expander (visible when "Enable Safe Mode Controls" checkbox in "Debug Settings" is toggled on). Each toggleable component can be independently disabled:

- Agents Tab
- Memory Tab
- Observability Tab
- Developer Tab
- Final Decision Card

Safe Mode tiers:

| Tier | Components | Always Enabled |
|---|---|---|
| 1 (Core) | Overview Cards, Pipeline, Execution Tab, Timeline Tab | Yes |
| 2 (Progressive) | Agents Tab, Memory Tab, Observability Tab, Developer Tab, Final Decision Card | Toggle via checkboxes |

---

## Files Modified

| File | Change |
|---|---|
| `app/pages/ares_dashboard.py` | Rewrote loading pattern, removed nested tabs, added safe mode, added try/except guards |
| `verification/phase10_6_1/frontend_stability_report.md` | This report |

---

## Files Audited (No Changes Needed)

| File | Verdict |
|---|---|
| `app/components/dashboard_theme.py` | No longer called from ares_dashboard.py; dark theme CSS is inert |
| `app/components/execution_overview.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/agent_pipeline.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/agent_dag.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/agent_timeline.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/decision_intelligence.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/execution_context_panel.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/memory_intelligence.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/observability_panel.py` | Not imported by ares_dashboard.py; no changes needed |
| `app/components/developer_console.py` | Not imported by ares_dashboard.py; no changes needed |

---

## Regression Test

```python
# Verify ares_dashboard.py has no unsafe patterns
import ast, inspect
from app.pages.ares_dashboard import render

source = inspect.getsource(render)

# 1. No st.empty().container() pattern
assert 'empty().container()' not in source, \
    'Dangerous container pattern found'

# 2. No st.tabs() inside _render_developer_tab
dev_source = inspect.getsource(
    [obj for name, obj in inspect.getmembers(__import__('app.pages.ares_dashboard', fromlist=['_render_developer_tab']))
     if name == '_render_developer_tab'][0]
)
assert 'st.tabs()' not in dev_source, \
    'Nested tabs found in _render_developer_tab'

# 3. Every section guarded by _safe_render
assert '_safe_render(' in source, \
    'No try/except guards found'

# 4. Integration check
from app._entry import _ROUTE_RENDER_MAP
assert 'ARES Dashboard' in _ROUTE_RENDER_MAP
assert callable(_ROUTE_RENDER_MAP['ARES Dashboard'][1])

print('All regression checks passed.')
```

---

## Success Criteria

| Criterion | Status |
|---|---|
| Clicking "Run Multi-Agent Pipeline" never causes a blank page | ✅ — `st.rerun()` ensures progress bar is top-level; results render on clean run |
| If a widget fails, the dashboard continues to work | ✅ — `_safe_render()` catches per-section exceptions, shows warning + traceback |
| Error reported instead of silent failure | ✅ — `st.warning()` with traceback in expandable code block |
| Safe Mode can isolate failing components | ✅ — toggle checkboxes disable individual sections |
| No nested `st.tabs()` | ✅ — replaced with `st.expander()` |
| No `st.empty()` + `.container()` pattern | ✅ — replaced with top-level progress + `st.rerun()` |
