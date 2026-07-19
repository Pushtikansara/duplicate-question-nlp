from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from duplicate_question_app.error_logger import analyze_error_log, get_error_logger, load_error_log, mine_hard_examples


def render() -> None:
    st.title("Error Logger & Hard Example Mining")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Automatically log prediction errors for analysis. Mine hardest examples for model improvement.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Log Error", "View Error Log", "Hard Example Mining"])

    with tab1:
        st.subheader("Log a Prediction Error")
        with st.form("error_log_form"):
            q1 = st.text_area("Question 1", height=80)
            q2 = st.text_area("Question 2", height=80)
            col1, col2 = st.columns(2)
            with col1:
                pred = st.selectbox("Predicted", ["Non-Duplicate", "Duplicate"])
                pred_label = 0 if pred == "Non-Duplicate" else 1
            with col2:
                true = st.selectbox("True Label", ["Non-Duplicate", "Duplicate"])
                true_label = 0 if true == "Non-Duplicate" else 1

            prob_dup = st.slider("Duplicate Probability", 0.0, 1.0, 0.5, 0.01)
            confidence = st.slider("Confidence", 0.0, 1.0, 0.5, 0.01)
            model_name = st.text_input("Model Name", "Adaptive Ensemble V2")
            notes = st.text_area("Notes (optional)")

            if st.form_submit_button("Log Error", use_container_width=True):
                if pred_label != true_label:
                    logger = get_error_logger()
                    example = logger.log_error(
                        question1=q1,
                        question2=q2,
                        predicted_label=pred_label,
                        true_label=true_label,
                        prob_duplicate=prob_dup,
                        confidence=confidence,
                        model_name=model_name,
                        notes=notes,
                    )
                    st.success(f"Error logged: {example.q1[:50]}... vs {example.q2[:50]}...")
                else:
                    st.warning("Prediction matches true label - not an error")

    with tab2:
        st.subheader("Error Log Analysis")
        log_path = st.text_input("Log file path", "hard_examples.csv")

        if st.button("Analyze Log"):
            try:
                df = load_error_log(Path(log_path))
                if df.empty:
                    st.info("No errors logged yet")
                else:
                    analysis = analyze_error_log(df)
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Errors", analysis["total_errors"])
                    col2.metric("False Positives", analysis["false_positives"])
                    col3.metric("False Negatives", analysis["false_negatives"])
                    col4.metric("Avg Confidence", f"{analysis['confidence_stats']['mean']:.2%}")

                    st.subheader("Error Categories")
                    if analysis["error_categories"]:
                        cat_df = pd.DataFrame(list(analysis["error_categories"].items()), columns=["Category", "Count"])
                        st.bar_chart(cat_df.set_index("Category"))

                    st.subheader("Top Confident Errors")
                    if analysis["top_confident_errors"]:
                        st.dataframe(pd.DataFrame(analysis["top_confident_errors"]), use_container_width=True)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

    with tab3:
        st.subheader("Mine Hard Examples")
        log_path = st.text_input("Log file path", "hard_examples.csv", key="mine_log")
        strategy = st.selectbox("Mining strategy", ["confidence", "disagreement", "lexical", "balanced"])
        n = st.slider("Number of examples", 10, 500, 50)

        if st.button("Mine Examples"):
            try:
                df = load_error_log(Path(log_path))
                if df.empty:
                    st.info("No data to mine")
                else:
                    hard_df = mine_hard_examples(df, n=n, strategy=strategy)
                    st.dataframe(hard_df, use_container_width=True)

                    csv = hard_df.to_csv(index=False).encode()
                    st.download_button(
                        "Download Hard Examples", data=csv, file_name="hard_examples_mined.csv", mime="text/csv"
                    )
            except Exception as exc:
                st.error(f"Mining failed: {exc}")
