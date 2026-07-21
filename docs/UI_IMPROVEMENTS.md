# UI Improvements Report

**Date:** 2026-07-21

---

## Changes Made

### 1. Model Selector (Sidebar)
**Before:** Simple `st.selectbox` with 11 models — dropdown clipped, no search, no categories.
**After:** Search input + filtered selectbox + model count + category + model info expander.

Features:
- **Search by name** — real-time filtering as user types
- **Model categories** — Classical ML, Transformer, Bi-Encoder, Cross Encoder, Ensemble
- **Model count** — shows "N models | N total"
- **Model info expander** — category, status, params, size, accuracy, F1
- **Badge** — ★ for recommended model
- **No empty state confusion** — "No models match your search" with total count when filter returns nothing

### 2. Model Manager Page

| Feature | Before | After |
|---------|--------|-------|
| Model count shown | 9 (missing 2) | 11 (all models) |
| Search in table | No | Yes — text input filters table |
| Search in detail | Basic selectbox | Text search + filtered selectbox |
| Accuracy/F1 columns | Missing | Added |
| Prediction mode | 3 modes | 7 modes + inline help |

### 3. Performance Dashboard

| Feature | Before | After |
|---------|--------|-------|
| Tabs | 4 (Week 4, Week 3, Comparison, SIE) | 6 (+ Live Profiling, Cache) |
| Live profiling | Not available | Real-time timing report from Profiler |
| Cache stats | Not available | Hit rates, sizes, evictions for all 7 caches |
| Reset/clear controls | Not available | Reset Profiler, Clear All Caches buttons |

### 4. Prediction Page

| Feature | Before | After |
|---------|--------|-------|
| Prediction display | Raw metric | Styled card with color (green=duplicate, red=non-dup) |
| Strategy info | 1-line text | Explanation from fusion |
| Semantic panel | Basic expander | Collapsible with 3-column layout |
| Model/mode/device info | 1 caption | 3-column layout |
| Conflicts | Simple list | Table with severity |

### 5. Batch Prediction Page

| Feature | Before | After |
|---------|--------|-------|
| Progress | Simple spinner | Progress bar + ETA + avg latency + throughput |
| Batch size config | Fixed at 64 | Configurable 8-512 |
| Model/mode info | Single caption | 3-column layout |
| Status feedback | None during batch | Real-time updates every ~5% |

### 6. Semantic Debugger

| Feature | Before | After |
|---------|--------|-------|
| Cache status | Not shown | All 7 caches with hit rates |
| Pipeline timings | From Profiler metadata | Profiler report |
| Fusion strategy | Fixed to FUSION | Interactive selector with all 8 strategies |
| Fusion weights | Not shown | Table with percentages |
| Component scores | Not shown | Table |
| Confidence breakdown | Not shown | Raw scores, weights, weighted scores |
| Semantic graph | Not shown | When available from representation |
| Raw JSON toggle | Always shown | Controlled by checkbox |

### 7. CSS Design System

| Element | Before | After |
|---------|--------|-------|
| Metric cards | Plain metric() | Styled with hover, shadow, border |
| Sidebar radio | No highlight | Highlighted selected, hover effect |
| Forms | Plain | Focus states, border radius |
| Tabs | Plain | Better spacing, horizontal scroll |
| Spacing | Inconsistent | Uniform gap, padding |
| Responsive | None | Mobile-friendly breakpoints |
| Empty states | None | Informative messages |

---

## Model Selector Scrolling Fix

**Problem:** The Streamlit `st.selectbox` has limited dropdown height. When there are 11 models, the dropdown clipped at the bottom of the sidebar. Users reported "when we scroll that not show" — models at the bottom of the list were hidden.

**Solution:** Added a search text input that filters the selectbox options before display. The user types part of the model name and only matching models appear in the dropdown. This:
- Eliminates scrolling through 11 items
- Works for long model names
- Never hides valid models (they appear when the search matches)
- Shows total count to reassure users all models are present

The search filters by model display name. Future improvement could also search by internal_id, aliases, and description.
