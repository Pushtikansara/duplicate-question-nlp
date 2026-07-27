from __future__ import annotations

from typing import Any

import streamlit as st


def render_agent_timeline(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Agent Timeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Execution duration per agent — hover for exact timing</div>',
        unsafe_allow_html=True,
    )

    agents_data = result.get("agent_timeline", [])
    if not agents_data:
        agents_data = _build_timeline_from_result(result)

    if not agents_data:
        st.markdown(
            '<div class="glass-card-sm" style="text-align:center;padding:2rem;color:#8A8F98;">'
            "No timeline data available.</div>",
            unsafe_allow_html=True,
        )
        return

    total_ms = max((a.get("duration_ms", 0) for a in agents_data), default=1)

    colors = {
        "planner": "#5E6AD2",
        "predict": "#22C55E",
        "semantic": "#3B82F6",
        "memory": "#F59E0B",
        "reflection": "#A78BFA",
        "decision": "#EC4899",
        "task_decomposer": "#5E6AD2",
        "capability": "#8B5CF6",
        "selector": "#6366F1",
        "scheduler": "#06B6D4",
    }

    for i, agent in enumerate(agents_data):
        name = agent.get("agent_id", agent.get("task_type", "unknown"))
        duration = agent.get("duration_ms", 0)
        status = agent.get("status", "completed")
        error = agent.get("error")

        color = colors.get(name.lower(), colors.get("planner"))
        width_pct = max((duration / total_ms) * 100, 2) if total_ms > 0 else 0

        dur_label = f"{duration:.0f}ms" if duration else "—"
        status_icon = "✓" if status == "SUCCESS" else "✗" if status == "FAILED" else "○"

        st.markdown(
            f"""
            <div class="animate-fade" style="animation-delay:{i * 0.06}s;">
                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:4px;">
                    <div style="min-width:100px;font-size:0.75rem;font-weight:500;color:var(--foreground);">
                        {status_icon} {name.replace("_", " ").title()}
                    </div>
                    <div style="flex:1;">
                        <div class="timeline-bar" title="{dur_label}">
                            <div class="timeline-bar-fill" style="width:{width_pct}%;background:{color};{"opacity:0.4;" if status == "FAILED" else ""}"></div>
                        </div>
                    </div>
                    <div style="min-width:60px;text-align:right;font-size:0.7rem;color:var(--foreground-muted);font-weight:500;">
                        {dur_label}
                    </div>
                </div>
                {f'<div style="margin:-2px 0 6px 108px;font-size:0.65rem;color:var(--error);">{error}</div>' if error else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="margin-top:8px;font-size:0.7rem;color:var(--foreground-muted);text-align:right;">'
        f"Total: {total_ms:.0f}ms</div>",
        unsafe_allow_html=True,
    )


def _build_timeline_from_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    timeline = result.get("timeline", {})
    agents: list[dict[str, Any]] = []

    phase_map = {
        "decomposition_ms": ("planner", 0),
        "prediction_ms": ("predict", 0),
        "semantic_validation_ms": ("semantic", 0),
        "memory_ms": ("memory", 0),
        "reflection_ms": ("reflection", 0),
        "decision_ms": ("decision", 0),
    }

    for key, (agent_id, _) in phase_map.items():
        dur = timeline.get(key, 0)
        if dur:
            agents.append(
                {
                    "agent_id": agent_id,
                    "task_type": agent_id.upper(),
                    "duration_ms": dur,
                    "status": "SUCCESS",
                }
            )

    decision = result.get("decision", {})
    if decision:
        agents.append(
            {
                "agent_id": "decision",
                "task_type": "DECIDE",
                "duration_ms": timeline.get("decision_ms", timeline.get("decision", 0)),
                "status": "SUCCESS",
                "confidence": decision.get("final_confidence", 0),
            }
        )

    return agents
