from __future__ import annotations

from typing import Any

import streamlit as st

PIPELINE_STEPS = [
    ("Planner", "planner", "Goal decomposition & strategy"),
    ("Task Decomposer", "task_decomposer", "Atomic task breakdown"),
    ("Capability Resolver", "capability", "Task→capability mapping"),
    ("Agent Selector", "selector", "Dynamic agent selection"),
    ("Execution Scheduler", "scheduler", "Dependency scheduling"),
    ("Parallel Tasks", "parallel", "Concurrent execution"),
    ("Decision Agent", "decision", "Confidence fusion"),
    ("Reflection", "reflection", "Trust assessment"),
]

STEP_ORDER = {
    "planning": 0,
    "decomposition": 1,
    "capability": 2,
    "selector": 3,
    "scheduler": 4,
    "parallel": 5,
    "decision": 6,
    "reflection": 7,
}


def render_agent_pipeline(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Agent Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">End-to-end multi-agent execution flow</div>', unsafe_allow_html=True)

    timeline_data = result.get("timeline", {})
    phase_timings = {k: v for k, v in timeline_data.items() if k.endswith("_ms") and v}
    decision = result.get("decision", {})

    step_statuses = _compute_step_statuses(result, phase_timings)

    cols = st.columns(len(PIPELINE_STEPS))
    for i, (name, step_id, desc) in enumerate(PIPELINE_STEPS):
        status_info = step_statuses.get(step_id, {"status": "pending", "duration": None})
        is_completed = status_info["status"] == "completed"
        is_running = status_info["status"] == "running"
        duration = status_info.get("duration")

        if step_id == "decision":
            tool_name = decision.get("recommendation", "—")
            output = f"{decision.get('final_confidence', 0):.0%}" if decision.get("final_confidence") else None
        elif step_id == "reflection":
            ref = result.get("reflection", {})
            tool_name = f"trust: {ref.get('trust_score', 0):.0%}" if ref.get("trust_score") else "—"
            output = ref.get("trust_level", "")
        elif step_id == "planner":
            tool_name = result.get("decomposition", {}).get("task_count", "—")
            output = f"{result.get('decomposition', {}).get('task_count', 0)} tasks"
        else:
            tool_name = "—"
            output = None

        with cols[i]:
            border_accent = (
                "rgba(94,106,210,0.4)"
                if is_completed
                else "rgba(245,158,11,0.3)"
                if is_running
                else "rgba(255,255,255,0.06)"
            )
            bg_accent = "rgba(94,106,210,0.08)" if is_completed else "rgba(245,158,11,0.05)" if is_running else ""

            pulse = "execution-pulse" if is_running else ""
            st.markdown(
                f"""
                <div class="pipeline-node {pulse}" style="border-color:{border_accent};background:{bg_accent};animation-delay:{i * 0.08}s;min-height:120px;">
                    <div style="font-size:0.7rem;font-weight:600;color:{"#5E6AD2" if is_completed else "#8A8F98"};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">
                        {("✓ " if is_completed else "○ ")}{name}
                    </div>
                    <div style="font-size:0.65rem;color:#8A8F98;margin-bottom:6px;">{desc}</div>
                    <div style="font-size:0.6rem;color:#6B7280;">
                        {f"<div>tool: {tool_name}</div>" if tool_name != "—" else ""}
                        {f"<div>→ {output}</div>" if output else ""}
                        {f"<div style='margin-top:2px;color:#5E6AD2;'>{duration:.0f}ms</div>" if duration else ""}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if i < len(PIPELINE_STEPS) - 1:
                arrow_color = "rgba(94,106,210,0.3)" if is_completed else "rgba(255,255,255,0.08)"
                st.markdown(
                    f"<div style='text-align:center;color:{arrow_color};font-size:1.2rem;margin:-4px 0;'>↓</div>",
                    unsafe_allow_html=True,
                )


def _compute_step_statuses(result: dict[str, Any], phase_timings: dict[str, float]) -> dict[str, dict]:
    statuses: dict[str, dict] = {}
    prediction = result.get("prediction", {})
    decision = result.get("decision", {})
    reflection = result.get("reflection", {})

    if prediction and "error" not in prediction:
        statuses["planner"] = {"status": "completed", "duration": phase_timings.get("decomposition_ms")}
        statuses["task_decomposer"] = {"status": "completed", "duration": phase_timings.get("decomposition_ms")}
        statuses["capability"] = {"status": "completed"}
        statuses["selector"] = {"status": "completed"}
    else:
        statuses["planner"] = {"status": "running"}

    if prediction and "error" not in prediction:
        statuses["scheduler"] = {"status": "completed"}
        statuses["parallel"] = {"status": "completed", "duration": phase_timings.get("prediction_ms")}
    else:
        statuses["scheduler"] = {"status": "pending"}
        statuses["parallel"] = {"status": "pending"}

    if decision and decision.get("final_confidence") is not None:
        statuses["decision"] = {"status": "completed", "duration": phase_timings.get("decision_ms")}
    else:
        statuses["decision"] = {"status": "pending"}

    if reflection and "error" not in reflection:
        statuses["reflection"] = {"status": "completed", "duration": phase_timings.get("reflection_ms")}
    else:
        statuses["reflection"] = {"status": "pending"}

    return statuses
