from __future__ import annotations

from typing import Any

import streamlit as st

from app.components.dashboard_theme import DAG_HTML_TEMPLATE


def render_execution_dag(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Execution DAG</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Interactive dependency graph — zoom, pan, hover for details</div>',
        unsafe_allow_html=True,
    )

    dag_data = result.get("execution_dag", [])
    if not dag_data:
        decomposition = result.get("decomposition", {})
        tasks = decomposition.get("tasks", [])
        dag_nodes = []
        for t in tasks:
            task_result = _find_task_result(result, t["task_id"])
            dag_nodes.append(
                {
                    "id": t["task_id"],
                    "label": t["task_type"],
                    "agent": t.get("agent_id", ""),
                    "status": _dag_status(task_result),
                    "duration": _task_duration(result, t["task_type"]),
                    "tool": _task_tool(t["task_type"]),
                }
            )
        dag_edges = []
        for t in tasks:
            for dep in t.get("depends_on", []):
                dag_edges.append(
                    {
                        "source": dep,
                        "target": t["task_id"],
                        "status": "completed" if _find_task_result(result, t["task_id"]) else "pending",
                    }
                )
    else:
        dag_nodes = [
            {
                "id": e["task_id"],
                "label": e["task_type"],
                "agent": e.get("agent_id", ""),
                "status": e.get("status", "pending"),
                "duration": e.get("duration_ms", 0),
                "tool": _task_tool(e["task_type"]),
            }
            for e in dag_data
        ]
        dag_edges = []
        for e in dag_data:
            for dep in e.get("depends_on", []):
                dag_edges.append({"source": dep, "target": e["task_id"], "status": e.get("status", "pending")})

    if not dag_nodes:
        st.markdown(
            '<div class="glass-card-sm" style="text-align:center;padding:2rem;color:#8A8F98;">'
            "No execution DAG data available. Run a multi-agent demo first.</div>",
            unsafe_allow_html=True,
        )
        return

    import json

    nodes_json = json.dumps(dag_nodes)
    edges_json = json.dumps(dag_edges)

    html = DAG_HTML_TEMPLATE.replace("{nodes}", nodes_json).replace("{edges}", edges_json)
    st.components.v1.html(html, height=420)

    with st.expander("Raw DAG Data", expanded=False):
        st.json({"nodes": dag_nodes, "edges": dag_edges})


def _find_task_result(result: dict[str, Any], task_id: str) -> dict | None:
    task_results = result.get("task_results", {})
    return task_results.get(task_id)


def _dag_status(task_result: dict | None) -> str:
    if task_result is None:
        return "pending"
    return "completed" if task_result.get("success") else "failed"


def _task_duration(result: dict[str, Any], task_type: str) -> float:
    tl = result.get("timeline", {})
    for k, v in tl.items():
        if task_type.lower() in k.lower() and isinstance(v, (int, float)):
            return v
    return 0


def _task_tool(task_type: str) -> str:
    tools = {
        "VALIDATE_INPUT": "—",
        "SELECT_MODEL": "—",
        "PREDICT": "predict",
        "SEMANTIC_VALIDATE": "—",
        "CALIBRATE": "—",
        "MEMORY_STORE": "memory",
        "MEMORY_RETRIEVE": "memory",
        "REFLECT": "reflection",
        "DECIDE": "—",
        "ENCODE_QUESTIONS": "—",
    }
    return tools.get(task_type, "—")
