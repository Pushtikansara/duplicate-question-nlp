from __future__ import annotations

from typing import Any

import streamlit as st


def render_observability(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Observability</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Execution metrics and system telemetry</div>',
        unsafe_allow_html=True,
    )

    obs = result.get("observability", {})
    timeline = result.get("timeline", {})

    total_tasks = obs.get("total_tasks", 0)
    succeeded = obs.get("succeeded", 0)
    failed = obs.get("failed", 0)
    success_rate = obs.get("success_rate", 0)
    avg_duration = obs.get("avg_duration_ms", 0)

    cols = st.columns(5)
    obs_metrics = [
        ("Tasks", str(total_tasks), "info"),
        ("Succeeded", str(succeeded), "success"),
        ("Failed", str(failed), "error" if failed else "info"),
        ("Success Rate", f"{success_rate:.0%}", "success" if success_rate >= 0.8 else "warning"),
        ("Avg Duration", f"{avg_duration:.0f}ms", "accent"),
    ]
    for i, (label, value, badge_type) in enumerate(obs_metrics):
        with cols[i]:
            st.markdown(
                f"""
                <div class="glass-card-sm animate-fade" style="text-align:center;animation-delay:{i * 0.06}s;">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value"><span class="badge badge-{badge_type}">{value}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div style="margin:0.75rem 0;"></div>', unsafe_allow_html=True)

    agents = obs.get("agents_used", [])
    task_types = obs.get("task_types", [])
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="glass-card-sm animate-fade">
                <div style="font-size:0.7rem;font-weight:600;color:var(--foreground-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;">Agents Used</div>
                <div style="display:flex;flex-wrap:wrap;gap:4px;">
                    {"".join(f'<span class="badge badge-accent">{a}</span>' for a in agents) if agents else '<span style="font-size:0.7rem;color:#8A8F98;">None</span>'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="glass-card-sm animate-fade" style="animation-delay:0.1s;">
                <div style="font-size:0.7rem;font-weight:600;color:var(--foreground-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;">Task Types Executed</div>
                <div style="display:flex;flex-wrap:wrap;gap:4px;">
                    {"".join(f'<span class="badge badge-info">{t}</span>' for t in task_types) if task_types else '<span style="font-size:0.7rem;color:#8A8F98;">None</span>'}
                </div>
            </div>
            """,
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

    phase_colors = ["#5E6AD2", "#22C55E", "#3B82F6", "#F59E0B", "#A78BFA", "#EC4899"]

    st.markdown(
        '<div style="margin-top:12px;font-size:0.75rem;font-weight:600;color:var(--foreground-muted);">Phase Latency Breakdown</div>',
        unsafe_allow_html=True,
    )

    phase_vals = []
    for key, name in phase_names:
        val = timeline.get(key, 0)
        if val:
            phase_vals.append((name, val))

    if phase_vals:
        total_phase = sum(v for _, v in phase_vals)
        for i, (name, val) in enumerate(phase_vals):
            pct = (val / total_phase * 100) if total_phase > 0 else 0
            st.markdown(
                f"""
                <div class="animate-fade" style="animation-delay:{i * 0.05}s;">
                    <div style="display:flex;justify-content:space-between;font-size:0.7rem;margin-bottom:2px;">
                        <span style="color:var(--foreground);">{name}</span>
                        <span style="color:var(--foreground-muted);">{val:.0f}ms ({pct:.0f}%)</span>
                    </div>
                    <div class="gauge-container" style="height:4px;margin-bottom:4px;">
                        <div class="gauge-fill" style="width:{pct}%;background:{phase_colors[i % len(phase_colors)]};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
