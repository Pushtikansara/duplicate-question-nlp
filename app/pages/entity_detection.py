from __future__ import annotations

import pandas as pd
import streamlit as st

from duplicate_question_app.entity_detector import analyze_entity_mismatch


def render() -> None:
    st.title("Entity Detection Analysis")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Extract and compare entities (programming languages, frameworks, OS, companies, etc.) "
        "between two questions. Entity mismatches apply penalties to duplicate probability.</p>",
        unsafe_allow_html=True,
    )

    with st.form("entity_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Entities", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Extracting entities..."):
            try:
                result = analyze_entity_mismatch(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Entity Penalty", f"{result.mismatch_penalty:.2%}")
        col2.metric("Q1 Entities", len(result.q1_entities))
        col3.metric("Q2 Entities", len(result.q2_entities))
        col4.metric("Overlap Types", len(result.entity_overlap))

        tab1, tab2, tab3 = st.tabs(["Q1 Entities", "Q2 Entities", "Mismatches"])

        with tab1:
            if result.q1_entities:
                df = pd.DataFrame(
                    [
                        {"Type": e.entity_type, "Value": e.value, "Confidence": f"{e.confidence:.0%}"}
                        for e in result.q1_entities
                    ]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No entities detected in Question 1")

        with tab2:
            if result.q2_entities:
                df = pd.DataFrame(
                    [
                        {"Type": e.entity_type, "Value": e.value, "Confidence": f"{e.confidence:.0%}"}
                        for e in result.q2_entities
                    ]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No entities detected in Question 2")

        with tab3:
            if result.entity_mismatch:
                for etype, (q1_only, q2_only) in result.entity_mismatch.items():
                    if q1_only or q2_only:
                        st.write(
                            f"**{etype}**: Q1={sorted(q1_only) if q1_only else '—'} | Q2={sorted(q2_only) if q2_only else '—'}"
                        )
            if result.penalty_details:
                st.subheader("Penalty Details")
                for detail in result.penalty_details:
                    st.caption(detail)
