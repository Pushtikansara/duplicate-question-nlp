from __future__ import annotations

from typing import Any

import streamlit as st


def render_memory_intelligence(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Memory Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Working / short-term / long-term memory state</div>',
        unsafe_allow_html=True,
    )

    memory_data = result.get("memory", {})
    if not memory_data or memory_data == {"status": "skipped"}:
        st.markdown(
            '<div class="glass-card-sm" style="text-align:center;padding:2rem;color:#8A8F98;">'
            "No memory operations recorded.</div>",
            unsafe_allow_html=True,
        )
        return

    stored = memory_data.get("stored", {})
    retrieved_entries = memory_data.get("retrieved_entries", [])
    retrieved_count = memory_data.get("retrieved_count", len(retrieved_entries))

    cols = st.columns(3)
    cols[0].markdown(
        f"""
        <div class="glass-card-sm animate-fade" style="text-align:center;">
            <div class="metric-label">Memory Store</div>
            <div class="metric-value"><span class="badge badge-accent">{stored.get("memory_id", "—")[:8]}…</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        f"""
        <div class="glass-card-sm animate-fade" style="text-align:center;animation-delay:0.1s;">
            <div class="metric-label">Retrieved</div>
            <div class="metric-value"><span class="badge badge-info">{retrieved_count} entries</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols[2].markdown(
        f"""
        <div class="glass-card-sm animate-fade" style="text-align:center;animation-delay:0.2s;">
            <div class="metric-label">Key</div>
            <div class="metric-value" style="font-size:0.85rem;"><span class="badge badge-accent">{stored.get("key", "—")}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if retrieved_entries:
        st.markdown(
            '<div style="margin-top:12px;font-size:0.75rem;font-weight:600;color:var(--foreground-muted);">'
            "Retrieved Entries</div>",
            unsafe_allow_html=True,
        )
        for entry in retrieved_entries[:5]:
            tier = entry.get("tier", "—")
            score = entry.get("score", 0)
            tier_color = {
                "WORKING": "#5E6AD2",
                "SHORT_TERM": "#F59E0B",
                "LONG_TERM": "#22C55E",
            }.get(tier, "#8A8F98")

            st.markdown(
                f"""
                <div class="glass-card-sm animate-fade" style="padding:0.5rem 0.75rem;margin-bottom:4px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-size:0.65rem;color:var(--foreground-muted);">ID: </span>
                            <span style="font-size:0.7rem;color:var(--foreground);font-weight:500;">{entry.get("memory_id", "—")[:12]}…</span>
                        </div>
                        <div style="display:flex;gap:8px;align-items:center;">
                            <span class="badge badge-accent" style="font-size:0.6rem;background:{tier_color}20;color:{tier_color};">{tier}</span>
                            <span style="font-size:0.7rem;color:var(--foreground-muted);">score: {score:.2f}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_memory_badge(tier: str) -> str:
    colors = {
        "WORKING": "#5E6AD2",
        "SHORT_TERM": "#F59E0B",
        "LONG_TERM": "#22C55E",
    }
    c = colors.get(tier, "#8A8F98")
    return f'<span style="background:{c}20;color:{c};padding:2px 8px;border-radius:100px;font-size:0.6rem;font-weight:500;">{tier}</span>'
