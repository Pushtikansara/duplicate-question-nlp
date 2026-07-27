from __future__ import annotations

from typing import Any

import streamlit as st


def render_developer_console(result: dict[str, Any]) -> None:
    with st.expander("Developer Console", expanded=False):
        tabs = st.tabs(["Execution Context", "Agent Messages", "Decision Output", "Diagnostics"])

        with tabs[0]:
            _render_context_json(result)

        with tabs[1]:
            _render_messages(result)

        with tabs[2]:
            _render_decision_detail(result)

        with tabs[3]:
            _render_diagnostics(result)


def _render_context_json(result: dict[str, Any]) -> None:
    context = {
        "trace_id": result.get("trace_id", ""),
        "scenario_id": result.get("scenario_id", ""),
        "status": result.get("status", ""),
        "goal": result.get("goal", {}),
        "input": result.get("input", {}),
        "strategy": result.get("strategy", result.get("goal", {}).get("strategy", "")),
        "total_time_ms": result.get("total_time_ms", result.get("timeline", {}).get("total_ms", 0)),
        "decomposition": result.get("decomposition", {}),
    }
    _render_json("Execution Context", context)


def _render_messages(result: dict[str, Any]) -> None:
    events = result.get("events", [])
    if events:
        st.markdown(
            '<div style="font-size:0.75rem;font-weight:600;color:var(--foreground-muted);margin-bottom:8px;">'
            f"Event Stream ({len(events)} events)</div>",
            unsafe_allow_html=True,
        )
        for ev in events[:20]:
            st.markdown(
                f"""
                <div class="glass-card-sm" style="padding:0.4rem 0.6rem;margin-bottom:3px;">
                    <div style="display:flex;gap:8px;font-size:0.7rem;">
                        <span style="color:var(--accent);">[{ev.get("source", "?")}]</span>
                        <span style="color:var(--foreground);">{ev.get("event_type", "?")}</span>
                        <span style="color:var(--foreground-muted);margin-left:auto;">{ev.get("timestamp", "")[:19] if ev.get("timestamp") else ""}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="font-size:0.75rem;color:#8A8F98;">No events captured.</div>',
            unsafe_allow_html=True,
        )


def _render_decision_detail(result: dict[str, Any]) -> None:
    decision = result.get("decision", {})
    prediction = result.get("prediction", {})
    semantic = result.get("semantic_validation", {})
    reflection = result.get("reflection", {})

    detail = {
        "prediction": {
            "label": prediction.get("predicted_label"),
            "prediction": prediction.get("prediction"),
            "confidence": prediction.get("confidence"),
            "model": prediction.get("model_name"),
            "latency_ms": prediction.get("latency_ms"),
        },
        "semantic_validation": {
            "adjusted_confidence": semantic.get("adjusted_confidence"),
            "ambiguity_detected": semantic.get("ambiguity_detected"),
            "entity_overlap": semantic.get("entity_overlap"),
        },
        "reflection": {
            "trust_score": reflection.get("trust_score"),
            "trust_level": reflection.get("trust_level"),
            "risk_level": reflection.get("risk_level"),
            "human_review_required": reflection.get("human_review_required"),
        },
        "decision": {
            "prediction": decision.get("prediction"),
            "raw_confidence": decision.get("raw_confidence"),
            "adjusted_confidence": decision.get("adjusted_confidence"),
            "trust_score": decision.get("trust_score"),
            "final_confidence": decision.get("final_confidence"),
            "recommendation": decision.get("recommendation"),
            "signals": decision.get("signals", []),
            "conflicts": decision.get("conflicts", []),
        },
    }
    _render_json("Decision Detail", detail)


def _render_diagnostics(result: dict[str, Any]) -> None:
    diagnostics = {
        "trace_id": result.get("trace_id", ""),
        "multi_agent": result.get("multi_agent", False),
        "agent_selection": {
            "total_active": result.get("agent_selection", {}).get("total_active", 0),
            "agents": [
                {"agent_id": a.get("agent_id"), "capabilities": a.get("capabilities", [])}
                for a in result.get("agent_selection", {}).get("agents", [])
            ],
        },
        "tool_discovery": result.get("tool_discovery", []),
        "cache_stats": result.get("cache_stats", {}),
        "events_count": len(result.get("events", [])),
    }
    _render_json("Diagnostics", diagnostics)


def _render_json(title: str, data: Any) -> None:
    st.markdown(
        f"""
        <div class="json-viewer" style="max-height:400px;overflow-y:auto;">
            {_format_json(data)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_json(data: Any, indent: int = 0) -> str:
    prefix = "  " * indent
    if data is None:
        return f'<span class="null">{prefix}null</span>'
    if isinstance(data, bool):
        return f'<span class="boolean">{prefix}{str(data).lower()}</span>'
    if isinstance(data, (int, float)):
        return f'<span class="number">{prefix}{data}</span>'
    if isinstance(data, str):
        escaped = data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<span class="string">{prefix}"{escaped}"</span>'
    if isinstance(data, dict):
        if not data:
            return f"{prefix}{{}}"
        parts = [f"{prefix}{{"]
        for k, v in data.items():
            parts.append(f'{prefix}  <span class="key">"{k}"</span>: {_format_json(v, indent + 1)}')
        parts.append(f"{prefix}}}")
        return "<br>".join(parts)
    if isinstance(data, (list, tuple)):
        if not data:
            return f"{prefix}[]"
        items = [_format_json(item, indent + 1) for item in data]
        parts = [f"{prefix}[", ",<br>".join(items), f"{prefix}]"]
        return "<br>".join(parts)
    return str(data)
