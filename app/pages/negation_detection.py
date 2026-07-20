from __future__ import annotations

import pandas as pd
import streamlit as st

from duplicate_question_app._linguistics.negation import detect_negations, get_negation_penalty


def render() -> None:
    st.title("Negation Detection")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Detect negation words (not, never, without, remove, disable, uninstall, delete, stop, prevent) "
        "that flip question meaning. Negation mismatches apply strong penalties.</p>",
        unsafe_allow_html=True,
    )

    with st.form("negation_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Negation", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Detecting negation..."):
            try:
                penalty, details = get_negation_penalty(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2 = st.columns(2)
        col1.metric("Negation Penalty", f"{penalty:.2%}")
        col2.metric("Details", details)

        q1_negs = detect_negations(q1)
        q2_negs = detect_negations(q2)

        tab1, tab2 = st.tabs(["Q1 Negations", "Q2 Negations"])
        with tab1:
            if q1_negs:
                df = pd.DataFrame(
                    [
                        {
                            "Text": n.text,
                            "Type": n.negation_type,
                            "Scope": n.scope.value,
                            "Confidence": f"{n.confidence:.0%}",
                            "Target": n.target or "—",
                        }
                        for n in q1_negs
                    ]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No negations detected in Question 1")

        with tab2:
            if q2_negs:
                df = pd.DataFrame(
                    [
                        {
                            "Text": n.text,
                            "Type": n.negation_type,
                            "Scope": n.scope.value,
                            "Confidence": f"{n.confidence:.0%}",
                            "Target": n.target or "—",
                        }
                        for n in q2_negs
                    ]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No negations detected in Question 2")
