from __future__ import annotations

from typing import Any

import streamlit as st


def render_execution_overview(result: dict[str, Any]) -> None:
    decision = result.get("decision", {})
    prediction = result.get("prediction", {})
    timeline = result.get("timeline", {})
    strategy = result.get("goal", {}).get("strategy", "N/A")
    model = result.get("input", {}).get("model", "") or prediction.get("model_name", "N/A")

    agents = result.get("agent_selection", {}).get("agents", [])
    total_agents = len(agents)
    decomposition = result.get("decomposition", {})
    total_tasks = decomposition.get("task_count", 0)
    parallel_groups = len(decomposition.get("parallel_groups", []))

    total_ms = timeline.get("total_ms", 0)
    final_conf = decision.get("final_confidence", prediction.get("confidence", 0))
    risk = prediction.get("risk_level", "unknown")

    cols = st.columns(8)
    cards = [
        ("Strategy", strategy, "accent"),
        ("Model", model if len(model) < 20 else model[:18] + "…", "info"),
        ("Agents", str(total_agents), "accent"),
        ("Parallel Groups", str(parallel_groups), "info"),
        ("Tasks", str(total_tasks), "accent"),
        ("Time", f"{total_ms:.0f}ms", "info"),
        ("Confidence", f"{final_conf:.1%}", "success" if final_conf >= 0.7 else "warning"),
        ("Risk", str(risk).upper(), "error" if risk == "HIGH" else "warning"),
    ]
    for i, (label, value, badge_type) in enumerate(cards):
        with cols[i]:
            st.markdown(
                f"""
                <div class="glass-card-sm animate-fade" style="text-align:center; animation-delay:{i * 0.05}s;">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value"><span class="badge badge-{badge_type}">{value}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_overview_cards(metrics: dict[str, Any]) -> None:
    cols = st.columns(6)
    for i, (label, value, badge_type) in enumerate(metrics):
        with cols[i]:
            st.markdown(
                f"""
                <div class="glass-card-sm animate-fade" style="text-align:center; animation-delay:{i * 0.05}s;">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value"><span class="badge badge-{badge_type}">{value}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
