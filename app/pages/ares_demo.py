from __future__ import annotations

import asyncio
from typing import Any

import streamlit as st

from ares.demo_engine import DemoEngine
from ares.demo_scenarios import DEMO_SCENARIOS


def _init_engine() -> DemoEngine:
    if "ares_demo_engine" not in st.session_state:
        engine = DemoEngine()
        engine.initialize()
        st.session_state["ares_demo_engine"] = engine
    return st.session_state["ares_demo_engine"]


def _render_header() -> None:
    st.markdown(
        """
        <div style="padding: 0.5rem 0;">
            <h1 style="margin:0; font-size:1.5rem; font-weight:700;">
                ARES Demo Pipeline
            </h1>
            <p style="margin:0.1rem 0 0 0; color:#64748B; font-size:0.85rem;">
                End-to-end demonstration of the ARES framework: Planning &rarr; Execution &rarr; Memory &rarr; Reflection
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _on_scenario_change() -> None:
    selected = st.session_state.get("ares_scenario_select")
    if selected and selected in DEMO_SCENARIOS:
        scenario = DEMO_SCENARIOS[selected]
        if not st.session_state.get("ares_q1_input"):
            st.session_state["ares_q1"] = scenario["question1"]
        if not st.session_state.get("ares_q2_input"):
            st.session_state["ares_q2"] = scenario["question2"]
        if not st.session_state.get("ares_goal_input"):
            st.session_state["ares_goal"] = scenario.get("goal", "")


def _render_scenario_selector() -> str | None:
    st.markdown("### Select Demo Scenario")
    scenario_ids = list(DEMO_SCENARIOS.keys())
    selected = st.selectbox(
        "Scenario",
        options=scenario_ids,
        format_func=lambda x: DEMO_SCENARIOS[x]["name"],
        index=0,
        key="ares_scenario_select",
        on_change=_on_scenario_change,
    )
    if selected:
        scenario = DEMO_SCENARIOS[selected]
        st.info(f"**{scenario['name']}**: {scenario['description']}")
        with st.expander("Scenario Details", expanded=False):
            st.json(scenario)
    return selected


def _render_custom_input() -> tuple[str, str, str]:
    st.markdown("### Custom Input")
    col1, col2 = st.columns(2)
    with col1:
        q1 = st.text_area(
            "Question 1",
            value=st.session_state.get("ares_q1", ""),
            height=80,
            key="ares_q1_input",
            placeholder="Enter first question...",
        )
    with col2:
        q2 = st.text_area(
            "Question 2",
            value=st.session_state.get("ares_q2", ""),
            height=80,
            key="ares_q2_input",
            placeholder="Enter second question...",
        )

    goal = st.text_input(
        "Goal (optional)",
        value=st.session_state.get("ares_goal", ""),
        key="ares_goal_input",
        placeholder="Custom goal for planning engine...",
    )
    return q1, q2, goal


def _render_execution_trace(result: dict[str, Any]) -> None:
    st.markdown("### Execution Trace")

    timeline = result.get("timeline", {})
    plan = result.get("plan", {})
    prediction = result.get("prediction", {})
    reflection = result.get("reflection", {})
    memory = result.get("memory", {})
    orchestration = result.get("orchestration", {})

    # Timeline metrics
    metrics_cols = st.columns(5)
    metrics_cols[0].metric("Planning", f"{timeline.get('planning_time_ms', 0):.0f}ms")
    metrics_cols[1].metric("Prediction", f"{timeline.get('prediction_time_ms', 0):.0f}ms")
    metrics_cols[2].metric("Memory", f"{timeline.get('memory_write_time_ms', 0):.0f}ms")
    metrics_cols[3].metric("Reflection", f"{timeline.get('reflection_time_ms', 0):.0f}ms")
    metrics_cols[4].metric("Total", f"{timeline.get('total_time_ms', 0):.0f}ms")

    # Planning Phase
    st.markdown("#### 1. Planning")
    with st.container(border=True):
        st.markdown(f"**Goal**: {result.get('goal', {}).get('description', 'N/A')}")
        strategy_info = result.get("strategy", {})
        st.markdown(f"**Requested Strategy**: `{strategy_info.get('requested', 'N/A')}`")
        st.markdown(f"**Resolved Strategy**: `{strategy_info.get('resolved', 'N/A')}`")
        st.markdown(f"**Graph Strategy**: `{plan.get('strategy', 'N/A')}`")
        if strategy_info.get("requested") != plan.get("strategy"):
            st.error(
                f"⚠️ STRATEGY MISMATCH: Requested `{strategy_info.get('requested')}` but Graph shows `{plan.get('strategy')}`"
            )
        st.markdown(f"**Nodes**: {plan.get('node_count', 0)} | **Edges**: {plan.get('edge_count', 0)}")
        st.markdown(f"**Validation Errors**: {len(result.get('validation_errors', []))}")

        if plan.get("execution_order"):
            st.markdown("**Execution Order**:")
            for level_idx, level in enumerate(plan["execution_order"]):
                level_nodes = ", ".join(
                    f"{n.get('action', '?')} ({n.get('node_id', '?')[:6]})"
                    for n in plan.get("nodes", [])
                    if n["node_id"] in level
                )
                st.text(f"  Level {level_idx}: [{level_nodes}]")

        with st.expander("Plan Graph", expanded=False):
            st.json(plan)

    # Prediction Phase
    st.markdown("#### 2. Prediction")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.write(f"**Q1**: {prediction.get('question1', '')}")
        col2.write(f"**Q2**: {prediction.get('question2', '')}")
        st.markdown(f"**Result**: **{prediction.get('prediction', 'N/A')}**")
        st.markdown(f"**Confidence**: {prediction.get('confidence', 0):.2%}")
        st.markdown(f"**Model**: {prediction.get('model_name', 'N/A')}")
        st.markdown(f"**Latency**: {prediction.get('latency_ms', 0):.1f}ms")

    # Memory Phase
    st.markdown("#### 3. Memory Operations")
    with st.container(border=True):
        st.markdown(f"**Stored**: `{memory.get('stored', {}).get('key', 'N/A')}`")
        st.markdown(f"**Retrieved**: {memory.get('retrieved_count', 0)} entries")
        with st.expander("Memory Entries", expanded=False):
            st.json(memory.get("retrieved_entries", []))

    # Reflection Phase
    st.markdown("#### 4. Reflection")
    with st.container(border=True):
        ref = reflection
        trust_score = ref.get("trust_score", 0) or 0
        trust_color = "green" if trust_score > 0.7 else "orange" if trust_score > 0.4 else "red"
        st.markdown(
            f"**Trust Score**: <span style='color:{trust_color};font-weight:bold;'>{trust_score:.2%}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Trust Level**: {ref.get('trust_level', 'N/A')}")
        st.markdown(f"**Risk Level**: {ref.get('risk_level', 'N/A')}")
        st.markdown(f"**Human Review**: {'⚠️ Required' if ref.get('human_review_required') else '✅ Not Required'}")
        if ref.get("recommendations"):
            st.markdown("**Recommendations**:")
            for r in ref["recommendations"]:
                st.markdown(f"- {r}")

    # Orchestration Phase
    st.markdown("#### 5. Orchestration")
    with st.container(border=True):
        orch_status = orchestration.get("status", "N/A")
        st.markdown(f"**Status**: {orch_status}")
        agent_results = orchestration.get("agent_results", [])
        if agent_results:
            st.markdown("**Agent Results**:")
            for ar in agent_results:
                st.markdown(
                    f"- **{ar.get('agent_id', '?')}**: {ar.get('status', '?')} "
                    f"({ar.get('processing_time_ms', 0):.0f}ms)"
                )

    # Events
    st.markdown("#### 6. Event Stream")
    events = result.get("events", [])
    with st.expander(f"Events ({len(events)})", expanded=False):
        for ev in events:
            st.text(f"[{ev.get('source', '?')}] {ev.get('event_type', '?')}")

    # Final Response
    st.markdown("#### Final Response")
    st.success(result.get("final_response", "No response"))


def render() -> None:
    _render_header()

    if "ares_scenario_defaults_initialized" not in st.session_state:
        first_id = list(DEMO_SCENARIOS.keys())[0]
        first = DEMO_SCENARIOS[first_id]
        st.session_state.setdefault("ares_q1", first["question1"])
        st.session_state.setdefault("ares_q2", first["question2"])
        st.session_state.setdefault("ares_goal", first.get("goal", ""))
        st.session_state["ares_scenario_defaults_initialized"] = True

    engine = _init_engine()

    scenario_id = _render_scenario_selector()
    q1, q2, goal = _render_custom_input()

    col1, col2 = st.columns([1, 5])
    with col1:
        strategy = st.selectbox(
            "Strategy", ["LINEAR", "TREE", "DAG", "GRAPH", "HIERARCHICAL", "AUTO"], index=0, key="ares_strategy"
        )

    run_clicked = st.button("Run ARES Demo", type="primary", use_container_width=True)

    if run_clicked:
        if scenario_id:
            scenario = DEMO_SCENARIOS.get(scenario_id)
            if scenario:
                if not q1:
                    q1 = scenario["question1"]
                if not q2:
                    q2 = scenario["question2"]
                if not goal:
                    goal = scenario.get("goal", goal)

        if not q1 or not q2:
            st.warning("Please enter both questions or select a scenario.")
            return

        with st.spinner("Running ARES demo pipeline..."):
            progress_bar = st.progress(0, text="Initializing...")
            try:

                async def run():
                    progress_bar.progress(10, text="Creating goal & plan...")
                    selected_model = st.session_state.get("selected_model")
                    result = await engine.run_demo(
                        scenario_id=scenario_id,
                        question1=q1,
                        question2=q2,
                        goal=goal or "Analyze semantic similarity between two questions",
                        strategy=strategy,
                        agent_ids=["planner", "predict", "memory", "reflection"],
                        available_tools=["predict", "memory"],
                        model_name=selected_model,
                    )
                    progress_bar.progress(100, text="Complete!")
                    return result

                result = asyncio.run(run())

                st.session_state["ares_q1"] = q1
                st.session_state["ares_q2"] = q2
                st.session_state["ares_goal"] = goal
                st.session_state["ares_last_result"] = result

                progress_bar.empty()
                _render_execution_trace(result)

            except Exception as e:
                progress_bar.empty()
                st.error(f"Demo failed: {e}")
                import traceback

                st.code(traceback.format_exc())

    elif "ares_last_result" in st.session_state:
        _render_execution_trace(st.session_state["ares_last_result"])

    # Bottom section: Inspect system state
    with st.expander("System State", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Refresh Tools"):
                tools = engine.get_tools()
                st.json(tools)
            if st.button("Refresh Agents"):
                agents = engine.get_agents()
                st.json(agents)
        with col2:
            if st.button("Refresh Memory"):
                memory_state = engine.get_memory()
                st.json(memory_state)
            if st.button("Refresh Events"):
                events = engine.get_events(limit=20)
                st.json(events)
        if st.button("Refresh Metrics"):
            metrics = engine.get_metrics()
            st.json(metrics)

    st.markdown("---")
    st.caption("ARES Demo Pipeline - Phase 10.5.1")
