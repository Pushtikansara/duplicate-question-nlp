from __future__ import annotations

import asyncio
from typing import Any

import pandas as pd
import streamlit as st

from ares.demo_engine import DemoEngine
from ares.demo_scenarios import DEMO_SCENARIOS
from ares.model_registry import build_registry


def _init_engine() -> DemoEngine:
    if "ares_dashboard_engine" not in st.session_state:
        engine = DemoEngine()
        engine.initialize()
        st.session_state["ares_dashboard_engine"] = engine
    return st.session_state["ares_dashboard_engine"]


def _render_overview_cards(result: dict[str, Any]) -> None:
    decision = result.get("decision", {})
    prediction = result.get("prediction", {})
    timeline = result.get("timeline", {})
    strategy = result.get("goal", {}).get("strategy", "N/A")
    model = result.get("input", {}).get("model", "") or prediction.get("model_name", "")
    decomposition = result.get("decomposition", {})
    mode = result.get("mode", "selected")
    fusion_data = result.get("fusion", {})

    tasks = decomposition.get("tasks", [])
    executed_agents = len({t.get("agent_id") for t in tasks if t.get("agent_id")})
    total_tasks = decomposition.get("task_count", len(tasks))
    total_ms = timeline.get("total_ms", 0)
    final_conf = decision.get("final_confidence", prediction.get("final_confidence", prediction.get("confidence", 0)))
    risk = prediction.get("risk_level", prediction.get("trust_level", ""))

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    col1.metric("Mode", "Fusion" if mode == "fusion" else "Selected")
    col2.metric("Strategy", strategy)
    col3.metric("Model", model or "Auto")
    col4.metric("Executed Agents", executed_agents)
    col5.metric("Tasks", total_tasks)
    col6.metric("Latency", f"{total_ms:.1f}ms" if total_ms else "N/A")
    col7.metric("Confidence", f"{final_conf:.1%}" if final_conf else "N/A")
    col8.metric("Risk", risk if risk else "N/A")

    if mode == "fusion" and fusion_data:
        st.markdown("#### Multi-Model Fusion")
        fusion_models = fusion_data.get("models", [])
        if fusion_models:
            cols = st.columns(len(fusion_models))
            for i, m in enumerate(fusion_models):
                with cols[i]:
                    label = "Dup" if m["predicted_label"] == 1 else "NonDup"
                    st.metric(m["model_name"][:20], f"{m['prob_duplicate']:.1%}", label)


def _render_execution_tab(result: dict[str, Any]) -> None:
    decision = result.get("decision", {})
    prediction = result.get("prediction", {})
    semantic = result.get("semantic_validation", {})
    confidence_calc = result.get("confidence_calculation", {})
    fusion_data = result.get("fusion", {})
    reflection = result.get("reflection", {})

    raw_conf = confidence_calc.get("raw_confidence", prediction.get("confidence"))
    adjusted_conf = confidence_calc.get("adjusted_confidence", semantic.get("adjusted_confidence", raw_conf))
    final_conf = confidence_calc.get("final_confidence", decision.get("final_confidence", raw_conf))
    trust_score = confidence_calc.get("trust_score", reflection.get("trust_score", prediction.get("trust_score")))
    recommendation = decision.get("recommendations", reflection.get("recommendations", []))

    col1, col2 = st.columns([1, 1])
    with col1:
        metrics_data = [
            ("Raw Confidence", raw_conf, "Initial prediction confidence before any calibration"),
            ("Calibrated (Semantic)", adjusted_conf, "After semantic validation adjustment"),
            ("Trust Score", trust_score, "Reflection engine trust assessment"),
            ("Final Confidence", final_conf, "Weighted combination using all signals"),
        ]
        for label, value, tooltip in metrics_data:
            if value is None:
                st.markdown(
                    f"<div class='dashboard-card' style='padding:0.5rem 0.75rem;margin-bottom:6px;'><div style='display:flex;justify-content:space-between;margin-bottom:4px;'><span style='font-size:0.7rem;color:var(--text-muted);'>{label}</span></div><div style='font-size:0.7rem;color:#F59E0B;'>Not available</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                pct = max(0, min(100, value * 100))
                level = "High" if value >= 0.7 else "Medium" if value >= 0.4 else "Low"
                level_color = "#10B981" if value >= 0.7 else "#F59E0B" if value >= 0.4 else "#EF4444"
                st.markdown(
                    f"<div class='dashboard-card' style='padding:0.5rem 0.75rem;margin-bottom:6px;'><div style='display:flex;justify-content:space-between;margin-bottom:4px;'><span style='font-size:0.7rem;color:var(--text-muted);' title='{tooltip}'>{label}</span><span style='font-size:0.7rem;font-weight:600;color:{level_color};'>{value:.1%} — {level}</span></div><div style='width:100%;height:4px;background:#E5E7EB;border-radius:4px;'><div style='width:{pct}%;height:100%;background:{level_color};border-radius:4px;'></div></div></div>",
                    unsafe_allow_html=True,
                )

    with col2:
        recs = (
            recommendation
            if isinstance(recommendation, list)
            else [recommendation]
            if recommendation
            else ["automatic_accept"]
            if trust_score and trust_score >= 0.7
            else ["review_manually"]
        )
        for rec in recs:
            rec_bg = "#DCFCE7" if rec == "automatic_accept" else "#FEF3C7" if "review" in rec else "#FEE2E2"
            rec_color = "#166534" if rec == "automatic_accept" else "#92400E" if "review" in rec else "#991B1B"
            st.markdown(
                f"<div class='dashboard-card' style='text-align:center;padding:0.75rem;margin-bottom:4px;'><span style='display:inline-block;padding:0.2rem 0.8rem;border-radius:100px;font-size:0.8rem;font-weight:500;background:{rec_bg};color:{rec_color};'>{rec.replace('_', ' ').title()}</span></div>",
                unsafe_allow_html=True,
            )

    explanation = result.get("explanation", {})
    if explanation and explanation.get("reasons"):
        with st.expander("Explanation", expanded=True):
            for reason in explanation["reasons"]:
                st.markdown(
                    f"<div style='font-size:0.8rem;color:var(--text-primary);padding:2px 0;'>• {reason}</div>",
                    unsafe_allow_html=True,
                )
            if explanation.get("summary"):
                st.markdown(
                    f"<div style='font-size:0.75rem;color:var(--text-muted);margin-top:6px;font-style:italic;'>{explanation['summary']}</div>",
                    unsafe_allow_html=True,
                )

    if fusion_data:
        with st.expander("Fusion Details", expanded=True):
            st.json(fusion_data)

    if semantic:
        with st.expander("Semantic Validation Details", expanded=False):
            st.json(semantic)

    if confidence_calc:
        with st.expander("Confidence Calculation", expanded=False):
            st.json(confidence_calc)


def _render_agents_tab(result: dict[str, Any]) -> None:
    tasks = result.get("decomposition", {}).get("tasks", [])
    agents = result.get("agent_selection", {}).get("agents", [])
    uncovered = result.get("agent_selection", {}).get("uncovered_capabilities", [])

    agent_caps: dict[str, list[str]] = {a["agent_id"]: a.get("capabilities", []) for a in agents}

    if tasks:
        rows = []
        for t in tasks:
            agent_id = t.get("agent_id", "")
            task_type = t.get("task_type", "")
            caps = agent_caps.get(agent_id, [])
            rows.append(
                {
                    "Task": task_type.replace("_", " ").title(),
                    "Selected Agent": agent_id or "Not assigned",
                    "Capability Match": ", ".join(caps) if caps else "General",
                    "Selection Score": len(caps) if caps else 0,
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

        total_active = result.get("agent_selection", {}).get("total_active", 0)
        total_registered = len(agent_caps)
        st.caption(
            f"Active agents: {total_active} | Total registered: {total_registered} | Tasks assigned: {len(tasks)}"
        )

        registry = build_registry()
        model_agents = [
            {"name": e.display_name, "type": e.backend.value, "status": e.status.value}
            for e in registry
            if e.status.value == "ready"
        ]
        if model_agents:
            with st.expander("Available Inference Models"):
                st.dataframe(
                    pd.DataFrame(model_agents).drop_duplicates(subset=["name"]), width="stretch", hide_index=True
                )
    else:
        registry = build_registry()
        model_agents = [
            {
                "name": e.display_name,
                "type": e.backend.value,
                "status": e.status.value,
                "capabilities": ", ".join(k for k, v in e.capabilities.__dict__.items() if v),
            }
            for e in registry
        ]
        st.dataframe(pd.DataFrame(model_agents), width="stretch", hide_index=True)

    if uncovered:
        with st.expander("Uncovered Capabilities"):
            for cap in uncovered:
                st.markdown(
                    f"<div style='font-size:0.75rem;color:#F59E0B;margin-bottom:2px;'>⚠ No agent has capability: <b>{cap}</b></div>",
                    unsafe_allow_html=True,
                )


def _render_timeline_tab(result: dict[str, Any]) -> None:
    timeline = result.get("timeline", {})
    total_ms = timeline.get("total_ms", 0)
    phase_names = [
        ("decomposition_ms", "Decomposition"),
        ("prediction_ms", "Prediction"),
        ("semantic_validation_ms", "Semantic Validation"),
        ("memory_ms", "Memory"),
        ("reflection_ms", "Reflection"),
        ("decision_ms", "Decision"),
    ]
    phase_colors = ["#2563EB", "#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899"]

    phase_vals = [
        (name, timeline.get(key))
        for key, name in phase_names
        if timeline.get(key) is not None and timeline.get(key) > 0
    ]
    if not phase_vals:
        st.info("No timing data recorded for this execution")
        return

    total_phase = sum(v for _, v in phase_vals)
    for i, (name, val) in enumerate(phase_vals):
        pct = (val / total_phase * 100) if total_phase > 0 else 0
        color = phase_colors[i % len(phase_colors)]
        st.markdown(
            f"<div style='margin-bottom:6px;'><div style='display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:2px;'><span style='color:var(--text-primary);font-weight:500;'>{name}</span><span style='color:var(--text-muted);'>{val:.1f}ms ({pct:.0f}%)</span></div><div style='width:100%;height:6px;background:#E5E7EB;border-radius:4px;'><div style='width:{pct}%;height:100%;background:{color};border-radius:4px;'></div></div></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='font-size:0.75rem;color:var(--text-muted);text-align:right;margin-top:4px;'>Total: {total_ms:.1f}ms</div>",
        unsafe_allow_html=True,
    )


def _render_memory_tab(result: dict[str, Any]) -> None:
    timeline = result.get("timeline", {})
    cache_stats = result.get("cache_stats", {})
    memory_ms = timeline.get("memory_ms", 0)
    memory_enabled = memory_ms > 0

    if not memory_enabled:
        st.info("Memory was not configured for this execution. Enable Memory in settings to store results.")
        return

    engine = _init_engine()
    col1, col2, col3, col4 = st.columns(4)
    mem_stats = engine.get_memory()
    mem_write_ops = len(mem_stats.get("entries", []))
    mem_read_ops = mem_stats.get("stats", {}).get("total_entries", 0)

    col1.metric("Memory Phase", "Executed")
    col2.metric("Write Ops", mem_write_ops)
    col3.metric("Read Ops", mem_read_ops)
    col4.metric("Latency", f"{memory_ms:.1f}ms")

    if cache_stats:
        st.markdown("#### Cache Statistics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Capacity", cache_stats.get("capacity", "N/A"))
        c2.metric("Size", cache_stats.get("size", "N/A"))
        c3.metric("TTL", f"{cache_stats.get('default_ttl_seconds', 0)}s")

    memory_data = engine.get_memory()
    if memory_data.get("entries"):
        st.markdown("#### Stored Memory Entries")
        entries_df = pd.DataFrame(memory_data["entries"])
        if not entries_df.empty:
            st.dataframe(entries_df, width="stretch", hide_index=True)
        stats = memory_data.get("stats", {})
        st.caption(f"Total: {stats.get('total_entries', 0)} entries | Tiers: {stats.get('entries_by_tier', {})}")


def _render_observability_tab(result: dict[str, Any]) -> None:
    obs = result.get("observability", {})
    timeline = result.get("timeline", {})
    decomposition = result.get("decomposition", {})
    agent_timeline = result.get("agent_timeline", [])
    cache_stats = result.get("cache_stats", {})

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tasks", obs.get("total_tasks", 0))
    col2.metric("Succeeded", obs.get("succeeded", 0))
    col3.metric("Failed", obs.get("failed", 0))
    col4.metric("Success Rate", f"{obs.get('success_rate', 0):.0%}" if obs.get("success_rate") is not None else "N/A")
    col5.metric("Avg Duration", f"{obs.get('avg_duration_ms', 0):.1f}ms" if obs.get("avg_duration_ms") else "N/A")

    total_failed = sum(1 for e in agent_timeline if e.get("status") == "FAILED")
    parallel_groups = decomposition.get("parallel_groups", [])
    col1, col2, col3 = st.columns(3)
    col1.metric("Retries (failed tasks)", total_failed)
    col2.metric("Parallel Groups", len(parallel_groups))
    col3.metric("Total Agents", len(agent_timeline))

    agents = obs.get("agents_used", [])
    task_types = obs.get("task_types", [])
    col1, col2 = st.columns(2)
    with col1:
        agent_badges = (
            "".join(
                f'<span style="display:inline-block;padding:0.15rem 0.55rem;border-radius:100px;font-size:0.7rem;font-weight:500;background:#DBEAFE;color:#1E40AF;margin:2px;">{a}</span>'
                for a in agents
            )
            if agents
            else '<span style="font-size:0.75rem;color:var(--text-muted);">None recorded</span>'
        )
        st.markdown(
            f"<div class='dashboard-card'><div style='font-size:0.7rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;'>Agents Used</div><div style='display:flex;flex-wrap:wrap;gap:4px;'>{agent_badges}</div></div>",
            unsafe_allow_html=True,
        )
    with col2:
        task_badges = (
            "".join(
                f'<span style="display:inline-block;padding:0.15rem 0.55rem;border-radius:100px;font-size:0.7rem;font-weight:500;background:#DCFCE7;color:#166534;margin:2px;">{t}</span>'
                for t in task_types
            )
            if task_types
            else '<span style="font-size:0.75rem;color:var(--text-muted);">None recorded</span>'
        )
        st.markdown(
            f"<div class='dashboard-card'><div style='font-size:0.7rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;'>Task Types</div><div style='display:flex;flex-wrap:wrap;gap:4px;'>{task_badges}</div></div>",
            unsafe_allow_html=True,
        )

    if cache_stats:
        st.markdown("#### Cache Statistics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Capacity", cache_stats.get("capacity", "N/A"))
        c2.metric("Size", cache_stats.get("size", "N/A"))
        c3.metric("TTL", f"{cache_stats.get('default_ttl_seconds', 0)}s")

    st.markdown("#### Phase Latency Breakdown")
    phase_names = [
        ("decomposition_ms", "Decomposition"),
        ("prediction_ms", "Prediction"),
        ("semantic_validation_ms", "Semantic"),
        ("memory_ms", "Memory"),
        ("reflection_ms", "Reflection"),
        ("decision_ms", "Decision"),
    ]
    phase_colors = ["#2563EB", "#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899"]
    phase_vals = [
        (name, timeline.get(key))
        for key, name in phase_names
        if timeline.get(key) is not None and timeline.get(key) > 0
    ]
    if phase_vals:
        total_phase = sum(v for _, v in phase_vals)
        for i, (name, val) in enumerate(phase_vals):
            pct = (val / total_phase * 100) if total_phase > 0 else 0
            bar_color = phase_colors[i % len(phase_colors)]
            st.markdown(
                f"<div style='margin-bottom:4px;'><div style='display:flex;justify-content:space-between;font-size:0.7rem;margin-bottom:2px;'><span style='color:var(--text-primary);'>{name}</span><span style='color:var(--text-muted);'>{val:.1f}ms ({pct:.0f}%)</span></div><div style='width:100%;height:4px;background:#E5E7EB;border-radius:4px;'><div style='width:{pct}%;height:100%;background:{bar_color};border-radius:4px;'></div></div></div>",
                unsafe_allow_html=True,
            )


def _render_developer_tab(result: dict[str, Any]) -> None:
    with st.expander("Execution Context", expanded=True):
        st.json(
            {
                "trace_id": result.get("trace_id"),
                "scenario_id": result.get("scenario_id"),
                "status": result.get("status"),
                "mode": result.get("mode"),
                "goal": result.get("goal"),
                "input": result.get("input"),
                "total_time_ms": result.get("total_time_ms", result.get("timeline", {}).get("total_ms", 0)),
                "decomposition": result.get("decomposition"),
            }
        )

    with st.expander("Decision Output", expanded=False):
        st.json(
            {
                "prediction": result.get("prediction", {}),
                "semantic_validation": result.get("semantic_validation", {}),
                "fusion": result.get("fusion", {}),
                "confidence_calculation": result.get("confidence_calculation", {}),
                "reflection": result.get("reflection", {}),
                "decision": result.get("decision", {}),
            }
        )

    with st.expander("Diagnostics", expanded=False):
        st.json(
            {
                "multi_agent": result.get("multi_agent"),
                "agent_selection": {
                    "total_active": result.get("agent_selection", {}).get("total_active"),
                    "agents": [
                        {"agent_id": a.get("agent_id"), "capabilities": a.get("capabilities", [])}
                        for a in result.get("agent_selection", {}).get("agents", [])
                    ],
                },
                "tool_discovery": result.get("tool_discovery"),
                "cache_stats": result.get("cache_stats"),
            }
        )


def _render_final_decision(result: dict[str, Any]) -> None:
    decision = result.get("decision", {})
    prediction = result.get("prediction", {})
    reflection = result.get("reflection", {})

    final_prediction = decision.get("prediction", prediction.get("prediction", ""))
    final_confidence = decision.get(
        "final_confidence", prediction.get("final_confidence", prediction.get("confidence"))
    )
    recommendation = decision.get(
        "recommendations",
        reflection.get(
            "recommendations",
            ["automatic_accept"] if (reflection.get("trust_score", 0) or 0) >= 0.7 else ["review_manually"],
        ),
    )

    if not final_prediction:
        return

    conf_color = (
        "#10B981"
        if final_confidence and final_confidence >= 0.7
        else "#F59E0B"
        if final_confidence and final_confidence >= 0.4
        else "#EF4444"
    )
    rec_label = (
        recommendation[0].replace("_", " ").title()
        if isinstance(recommendation, list) and recommendation
        else "Automatic"
    )
    rec_bg = (
        "#DCFCE7" if "accept" in str(recommendation) else "#FEF3C7" if "review" in str(recommendation) else "#FEE2E2"
    )
    rec_color = (
        "#166534" if "accept" in str(recommendation) else "#92400E" if "review" in str(recommendation) else "#991B1B"
    )

    st.markdown("<hr style='border-color:#E5E7EB;margin:1rem 0;'>", unsafe_allow_html=True)
    display_prediction = (
        final_prediction.title() if isinstance(final_prediction, str) and final_prediction else "Unknown"
    )
    st.markdown(
        f"<div class='dashboard-card' style='border-left:3px solid {conf_color};'><div style='display:flex;justify-content:space-between;align-items:center;'><div><div style='font-size:0.7rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.04em;'>Final Decision</div><div style='font-size:1.2rem;font-weight:700;color:var(--text-primary);margin-top:4px;'>{display_prediction} <span style='font-size:0.85rem;font-weight:500;color:{conf_color};'> ({final_confidence:.1%})</span></div></div><div style='text-align:right;'><span style='display:inline-block;padding:0.2rem 0.8rem;border-radius:100px;font-size:0.8rem;font-weight:500;background:{rec_bg};color:{rec_color};'>{rec_label}</span></div></div></div>",
        unsafe_allow_html=True,
    )


def _render_results(result: dict[str, Any]) -> None:
    _render_overview_cards(result)
    st.markdown("<hr style='border-color:#E5E7EB;margin:1rem 0;'>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Execution", "Agents", "Timeline", "Memory", "Observability", "Developer"]
    )
    with tab1:
        _render_execution_tab(result)
    with tab2:
        _render_agents_tab(result)
    with tab3:
        _render_timeline_tab(result)
    with tab4:
        _render_memory_tab(result)
    with tab5:
        _render_observability_tab(result)
    with tab6:
        _render_developer_tab(result)
    _render_final_decision(result)


def render() -> None:
    st.title("ARES Multi-Agent Intelligence")
    st.markdown(
        "<p style='color:#64748B;font-size:0.95rem;'>Autonomous Reasoning Execution System — real-time multi-agent orchestration for duplicate question detection.</p>",
        unsafe_allow_html=True,
    )

    engine = _init_engine()
    scenario_ids = list(DEMO_SCENARIOS.keys())

    with st.form("ares_pipeline_form"):
        st.markdown("#### Configuration")
        selected = st.selectbox(
            "Scenario",
            options=[""] + scenario_ids,
            format_func=lambda x: DEMO_SCENARIOS[x]["name"] if x else "Custom Input",
        )

        scenario = DEMO_SCENARIOS.get(selected) if selected else None

        col1, col2 = st.columns(2)
        with col1:
            q1 = st.text_area(
                "Question 1",
                value=scenario["question1"] if scenario else "",
                height=90,
                placeholder="Enter first question...",
            )
        with col2:
            q2 = st.text_area(
                "Question 2",
                value=scenario["question2"] if scenario else "",
                height=90,
                placeholder="Enter second question...",
            )

        goal = st.text_input(
            "Goal (optional)",
            value=scenario.get("goal", "") if scenario else "",
            placeholder="Custom goal for the planning engine...",
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            strategy = st.selectbox("Strategy", ["LINEAR", "TREE", "DAG", "GRAPH", "HIERARCHICAL"], index=0)
        with col2:
            mode = st.selectbox(
                "Execution Mode",
                ["selected", "fusion"],
                index=0,
                help="'selected' uses one model; 'fusion' runs all compatible models and combines results",
            )
        with col3:
            reflection_enabled = st.checkbox("Reflection", value=True)
        with col4:
            memory_enabled = st.checkbox("Memory", value=True)

        submitted = st.form_submit_button("Run Multi-Agent Pipeline", type="primary", use_container_width=True)

    if submitted:
        q1_final = q1
        q2_final = q2
        goal_final = goal
        if (not q1 or not q2) and scenario:
            q1_final = q1 or scenario["question1"]
            q2_final = q2 or scenario["question2"]
            goal_final = goal_final or scenario.get("goal", "")
        if not q1_final or not q2_final:
            st.warning("Please enter both questions or select a scenario.")
            return

        try:
            bar = st.progress(0, text="Initializing multi-agent pipeline...")

            async def run_agents() -> dict[str, Any]:
                bar.progress(10, text="Decomposing goal into atomic tasks...")
                result = await engine.run_multi_agent_demo(
                    scenario_id=selected,
                    question1=q1_final,
                    question2=q2_final,
                    goal=goal_final or "Analyze semantic similarity between two questions",
                    strategy=strategy,
                    mode=mode,
                    include_reflection=reflection_enabled,
                    include_memory=memory_enabled,
                    model_name=st.session_state.get("selected_model", "") or None,
                )
                return result

            result = asyncio.run(run_agents())
            st.session_state["ares_dashboard_result"] = result
            st.rerun()
        except Exception as e:
            st.error(f"Pipeline Error: {e}")
            import traceback

            st.code(traceback.format_exc())

    elif "ares_dashboard_result" in st.session_state:
        _render_results(st.session_state["ares_dashboard_result"])
        if st.button("Run New Pipeline", type="secondary"):
            for key in ["ares_dashboard_result"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        st.info(
            "Configure your input above, then run the pipeline to visualize task decomposition, agent selection, execution, and decision fusion."
        )
