from __future__ import annotations

from typing import Any

import streamlit as st


def render_execution_context(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Execution Context</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Developer panel — full execution parameters and state</div>',
        unsafe_allow_html=True,
    )

    input_data = result.get("input", {})
    goal = result.get("goal", {})
    strategy = goal.get("strategy", result.get("strategy", "N/A"))
    model = input_data.get("model", "") or result.get("prediction", {}).get("model_name", "N/A")
    decomposition = result.get("decomposition", {})

    cols = st.columns(3)

    with cols[0]:
        _render_field("Question 1", input_data.get("question1", "—"))
        _render_field("Question 2", input_data.get("question2", "—"))

    with cols[1]:
        _render_field("Goal", goal.get("description", "—"))
        _render_field("Strategy", strategy)
        _render_field("Model", model)

    with cols[2]:
        agent_sel = result.get("agent_selection", {})
        _render_field("Active Agents", str(agent_sel.get("total_active", 0)))
        _render_field("Task Count", str(decomposition.get("task_count", 0)))
        _render_field("Parallel Groups", str(len(decomposition.get("parallel_groups", []))))

    st.markdown('<div style="margin:0.75rem 0;"></div>', unsafe_allow_html=True)

    phase_timings = result.get("timeline", {})
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;color:var(--foreground-muted);margin-bottom:6px;">Phase Timings</div>',
        unsafe_allow_html=True,
    )
    phase_names = [
        ("decomposition_ms", "Decomposition"),
        ("prediction_ms", "Prediction"),
        ("semantic_validation_ms", "Semantic Validation"),
        ("memory_ms", "Memory"),
        ("reflection_ms", "Reflection"),
        ("decision_ms", "Decision"),
    ]
    for key, name in phase_names:
        val = phase_timings.get(key, 0)
        if val:
            st.markdown(
                f"""
                <div class="glass-card-sm" style="padding:0.3rem 0.6rem;margin-bottom:2px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.7rem;">
                        <span style="color:var(--foreground);">{name}</span>
                        <span style="color:var(--foreground-muted);font-weight:500;">{val:.0f}ms</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_field(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="glass-card-sm" style="padding:0.4rem 0.6rem;margin-bottom:4px;">
            <div style="font-size:0.65rem;color:var(--foreground-muted);text-transform:uppercase;letter-spacing:0.04em;">{label}</div>
            <div style="font-size:0.8rem;color:var(--foreground);font-weight:500;word-break:break-all;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
