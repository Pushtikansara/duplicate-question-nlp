from __future__ import annotations

import streamlit as st

from app.services.runtime import get_model_resolution, get_runtime_context
from app.utils.constants import PATHS, _model_cache
from duplicate_question_app._models.embeddings import clear_embedding_cache
from duplicate_question_app._models.registry import build_registry
from duplicate_question_app._models.week2 import check_week2_artifacts

ROUTE_MAP: dict[str, str] = {
    "\U0001f3e0 Home": "Landing Page",
    "\U0001f3af Prediction": "Prediction Page",
    "\U0001f4ca Batch CSV": "Batch CSV Prediction",
    "\U0001f4c9 Performance": "Performance Dashboard",
    "\U0001f9ea Entity Detection": "Entity Detection",
    "\U0001f9ea Intent Detection": "Intent Detection",
    "\U0001f9ea Negation Detection": "Negation Detection",
    "\U0001f9ea Contradiction Detection": "Contradiction Detection",
    "\U0001f9ea Lexical Penalty": "Lexical Penalty",
    "\U0001f504 Adaptive Ensemble": "Adaptive Ensemble V2",
    "\u2699\ufe0f Calibration": "Advanced Calibration",
    "\U0001f4a1 Explainability": "Advanced Explainability",
    "\U0001f4cb Agreement Dashboard": "Agreement Dashboard",
    "\U0001f52c Hard Example Mining": "Hard Example Mining",
    "\U0001f4a1 Semantic Debugger": "Semantic Debugger",
    "\U0001f517 Model Manager": "Model Manager",
    "\U0001f4ca Dataset Info": "Dataset Information",
    "\U0001f916 ARES Demo": "ARES Demo",
}


def get_route_map() -> dict[str, str]:
    return ROUTE_MAP


def _render_group_label(label: str) -> None:
    st.sidebar.markdown(
        f"<div style='font-size:0.7rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:0.08em;color:#64748B;margin:0.75rem 0 0.15rem 0;'>{label}</div>",
        unsafe_allow_html=True,
    )


def _build_model_data() -> list[dict]:
    registry = build_registry(PATHS)
    model_data = []
    for e in registry:
        cat = e.model_type.replace("-", " ").title()
        if "cross" in e.model_type.lower():
            cat = "Cross Encoder"
        elif "bi" in e.model_type.lower():
            cat = "Bi-Encoder"
        elif "classical" in e.model_type.lower():
            cat = "Classical ML"
        elif "ensemble" in e.model_type.lower():
            cat = "Ensemble"
        elif "transformer" in e.model_type.lower():
            cat = "Transformer"
        status = e.load_status
        size = f"{e.size_mb:.0f}MB" if e.size_mb else ""
        params = e.parameters if e.parameters != "N/A" else ""
        acc = f"{e.accuracy:.3f}" if e.accuracy else ""
        f1 = f"{e.f1_score:.3f}" if e.f1_score else ""
        badge = "★" if e.display_name == "Improved DistilBERT (Week 4)" else ""
        model_data.append(
            {
                "name": e.display_name,
                "category": cat,
                "status": status,
                "size": size,
                "params": params,
                "accuracy": acc,
                "f1": f1,
                "badge": badge,
                "internal_id": e.internal_id,
            }
        )
    return model_data


def _render_model_selector() -> None:
    model_data = _build_model_data()
    prev_model = st.session_state.get("selected_model", None)
    default_model = prev_model or "Improved DistilBERT (Week 4)"

    categories = {}
    for m in model_data:
        cat = m["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(m)

    search = st.sidebar.text_input(
        "Search models",
        placeholder="Type model name...",
        key="model_search",
        label_visibility="collapsed",
    )

    filtered_models = []
    for m in model_data:
        if search and search.lower() not in m["name"].lower():
            continue
        label = m["name"]
        extras = []
        if m["size"]:
            extras.append(m["size"])
        if m["badge"]:
            label = f"{label} {m['badge']}"
        if extras:
            label = f"{label} ({', '.join(extras)})"
        filtered_models.append((m["name"], label))

    if not filtered_models:
        st.sidebar.caption("No models match your search.")
        st.sidebar.caption(f"Total: {len(model_data)} models registered")
        return

    st.sidebar.caption(f"{len(filtered_models)} models | {len(model_data)} total")

    selected_names = [f[0] for f in filtered_models]

    current_idx = selected_names.index(default_model) if default_model in selected_names else 0

    def _on_model_change():
        st.session_state["selected_model"] = st.session_state.sidebar_model_selector
        _model_cache.clear()
        clear_embedding_cache()
        st.query_params["selected_model"] = st.session_state.sidebar_model_selector

    st.sidebar.selectbox(
        "Select model",
        options=selected_names,
        index=current_idx,
        format_func=lambda x: next((label for name, label in filtered_models if name == x), x),
        key="sidebar_model_selector",
        label_visibility="collapsed",
        on_change=_on_model_change,
    )

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = default_model

    with st.sidebar.expander("Model Info", expanded=False):
        selected = st.session_state.get("selected_model", default_model)
        entry = next((m for m in model_data if m["name"] == selected), None)
        if entry:
            st.caption(f"Category: {entry['category']}")
            st.caption(f"Status: {entry['status']}")
            if entry["params"]:
                st.caption(f"Params: {entry['params']}")
            if entry["size"]:
                st.caption(f"Size: {entry['size']}")
            if entry["accuracy"]:
                st.caption(f"Accuracy: {entry['accuracy']}")
            if entry["f1"]:
                st.caption(f"F1: {entry['f1']}")


def sidebar_navigation() -> str:
    st.sidebar.markdown(
        """
        <div style="padding:0.5rem 0 0.25rem 0;">
            <div style="font-size:1.1rem;font-weight:700;color:#0F172A;">
                \U0001f52c DQD
            </div>
            <div style="font-size:0.75rem;color:#64748B;margin-top:-0.15rem;">
                Duplicate Question Detection
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_groups: list[tuple[str, list[str]]] = [
        ("Core", ["\U0001f3e0 Home", "\U0001f3af Prediction", "\U0001f4ca Batch CSV", "\U0001f4c9 Performance"]),
        (
            "Linguistic Analysis",
            [
                "\U0001f9ea Entity Detection",
                "\U0001f9ea Intent Detection",
                "\U0001f9ea Negation Detection",
                "\U0001f9ea Contradiction Detection",
                "\U0001f9ea Lexical Penalty",
            ],
        ),
        (
            "Advanced",
            [
                "\U0001f504 Adaptive Ensemble",
                "\u2699\ufe0f Calibration",
                "\U0001f4a1 Explainability",
                "\U0001f4cb Agreement Dashboard",
                "\U0001f52c Hard Example Mining",
                "\U0001f4a1 Semantic Debugger",
            ],
        ),
        ("ARES", ["\U0001f916 ARES Demo"]),
        ("Information", ["\U0001f517 Model Manager", "\U0001f4ca Dataset Info"]),
    ]

    flat_pages: list[str] = []
    for _group_name, pages in nav_groups:
        for page in pages:
            flat_pages.append(page)

    current = st.session_state.get("current_page", "\U0001f3e0 Home")
    if current not in flat_pages:
        current = "\U0001f3e0 Home"

    for group_name, _pages in nav_groups:
        _render_group_label(group_name)

    selected = st.sidebar.radio(
        "Navigate",
        flat_pages,
        index=flat_pages.index(current),
        key="nav_radio",
        label_visibility="collapsed",
    )

    if selected != current:
        st.session_state["current_page"] = selected

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size:0.7rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#64748B;margin:0.5rem 0 0.25rem 0;'>Model</div>",
        unsafe_allow_html=True,
    )

    _render_model_selector()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size:0.7rem;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#64748B;margin:0.5rem 0 0.25rem 0;'>System</div>",
        unsafe_allow_html=True,
    )

    resolution = get_model_resolution()
    model_name = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    try:
        _, metadata, _ = get_runtime_context()
        if isinstance(metadata, dict):
            active_label = metadata.get("model_label", model_name)[:30]
        elif metadata:
            active_label = metadata.model_label[:30]
        else:
            active_label = model_name[:30]
    except Exception:
        active_label = model_name[:30]

    st.sidebar.caption(f"Active: **{active_label}**")

    pred_mode = st.session_state.get("prediction_mode", "fusion")
    mode_icons = {
        "cross_encoder_only": "🔴 CE",
        "semantic_only": "🟢 SIE",
        "fusion": "🔵 FUSION",
        "cross_encoder_dominant": "🔵 CE-DOM",
        "semantic_dominant": "🟢 SEM-DOM",
        "confidence_weighted": "🟣 CONF-W",
        "adaptive": "🟠 ADAPTIVE",
        "learned_weighting": "⚪ LEARNED",
    }
    st.sidebar.caption(f"Mode: **{mode_icons.get(pred_mode, pred_mode)}**")

    week2_ready = all(check_week2_artifacts(PATHS).values())
    st.sidebar.caption(
        f"W2: {'✅' if week2_ready else '❌'}  "
        f"W3: {'✅' if resolution.week3.ready else '❌'}  "
        f"W4: {'✅' if resolution.week4.ready else '❌'}"
    )

    return ROUTE_MAP.get(selected, "Landing Page")
