from __future__ import annotations

from typing import Any

import streamlit as st


def render_decision_intelligence(result: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Decision Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Multi-signal confidence fusion pipeline</div>',
        unsafe_allow_html=True,
    )

    decision = result.get("decision", {})
    prediction = result.get("prediction", {})
    semantic = result.get("semantic_validation", {})

    raw_conf = prediction.get("confidence", 0)
    adjusted_conf = semantic.get("adjusted_confidence", raw_conf)
    trust_score = decision.get("trust_score", prediction.get("trust_score", 0))
    final_conf = decision.get("final_confidence", raw_conf)

    signals = decision.get("signals", [])
    conflicts = decision.get("conflicts", [])
    recommendation = decision.get("recommendation", "—")

    cols = st.columns([1, 1])

    with cols[0]:
        _render_gauge("Raw Confidence", raw_conf, "#8B5CF6", 0)
        _render_gauge("Calibration / Semantic Adjustment", adjusted_conf, "#3B82F6", 1)
        _render_gauge("Trust Score", trust_score, "#A78BFA", 2)

    with cols[1]:
        _render_gauge("Final Confidence (Weighted)", final_conf, "#22C55E", 3)
        st.markdown(
            f"""
            <div class="glass-card-sm animate-fade" style="animation-delay:0.3s;text-align:center;padding:1.25rem;">
                <div style="font-size:0.7rem;font-weight:600;color:var(--foreground-muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Recommendation</div>
                <div style="font-size:1.2rem;font-weight:700;color:var(--foreground);">
                    <span class="badge badge-{"success" if recommendation == "automatic_accept" else "warning" if recommendation == "review_recommended" else "error"}">{recommendation.replace("_", " ").title()}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="margin:1rem 0;"></div>', unsafe_allow_html=True)

    sig_cols = st.columns(3)

    with sig_cols[0]:
        _render_confidence_card(
            "Raw → Adjusted",
            f"{raw_conf:.1%}",
            f"{adjusted_conf:.1%}",
            f"{'▸ Up' if adjusted_conf > raw_conf else '▸ Down'}",
        )
    with sig_cols[1]:
        _render_confidence_card(
            "Adjusted → Trust",
            f"{adjusted_conf:.1%}",
            f"{trust_score:.1%}",
            f"{'▸ Up' if trust_score > adjusted_conf else '▸ Down'}",
        )
    with sig_cols[2]:
        final_vs_pct = f"{(final_conf - raw_conf) * 100:+.1f}%"
        _render_confidence_card("Overall Fusion", f"{raw_conf:.1%}", f"{final_conf:.1%}", final_vs_pct)

    if signals:
        with st.expander("Decision Signals", expanded=False):
            for sig in signals:
                st.markdown(
                    f"<div style='font-size:0.75rem;color:var(--foreground-muted);margin-bottom:4px;'>"
                    f"<span style='color:var(--accent);'>●</span> "
                    f"<b>{sig.get('source', '?').replace('_', ' ').title()}</b>: "
                    f"{sig.get('type', '?').replace('_', ' ')} — "
                    f"from {sig.get('from', 0):.1%} to {sig.get('to', 0):.1%}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    if conflicts:
        with st.expander("Signal Conflicts", expanded=False):
            for c in conflicts:
                st.markdown(
                    f"<div style='font-size:0.75rem;color:var(--warning);margin-bottom:4px;'>"
                    f"⚠ {c.replace('_', ' ').title()}</div>",
                    unsafe_allow_html=True,
                )


def _render_gauge(label: str, value: float, color: str, delay: int) -> None:
    pct = max(0, min(100, value * 100))
    gauge_color = color if value >= 0.5 else "#EF4444"
    confidence_label = "High" if value >= 0.7 else "Medium" if value >= 0.4 else "Low"
    conf_color = "#22C55E" if value >= 0.7 else "#F59E0B" if value >= 0.4 else "#EF4444"

    st.markdown(
        f"""
        <div class="glass-card-sm animate-fade" style="margin-bottom:8px;animation-delay:{delay * 0.1}s;">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <div style="font-size:0.7rem;color:var(--foreground-muted);">{label}</div>
                <div style="font-size:0.7rem;font-weight:600;color:{conf_color};">{value:.0%} • {confidence_label}</div>
            </div>
            <div class="gauge-container">
                <div class="gauge-fill" style="width:{pct}%;background:{gauge_color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_confidence_card(title: str, from_val: str, to_val: str, delta: str) -> None:
    st.markdown(
        f"""
        <div class="glass-card-sm animate-fade" style="text-align:center;animation-delay:0.4s;">
            <div style="font-size:0.65rem;font-weight:600;color:var(--foreground-muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;">{title}</div>
            <div style="display:flex;justify-content:center;align-items:center;gap:8px;">
                <span style="font-size:1rem;font-weight:600;color:var(--foreground);">{from_val}</span>
                <span style="color:var(--accent);font-size:0.8rem;">→</span>
                <span style="font-size:1rem;font-weight:700;color:var(--success);">{to_val}</span>
            </div>
            <div style="font-size:0.65rem;color:var(--foreground-muted);margin-top:4px;">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
