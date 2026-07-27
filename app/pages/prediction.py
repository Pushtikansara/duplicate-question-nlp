from __future__ import annotations

import time

import streamlit as st

from app.utils.constants import get_model_prediction
from ares.inference.dispatcher import InferenceDispatcher
from duplicate_question_app._visualization.plots import create_probability_figure


def render() -> None:
    st.title("Prediction Page")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Run live inference on individual question pairs with the selected model.</p>",
        unsafe_allow_html=True,
    )
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    backend_name = InferenceDispatcher.get_backend_for_model(selected_model)

    col1, col2 = st.columns(2)
    col1.caption(f"Selected Model: **{selected_model}**")
    col2.caption(f"Backend: **{backend_name}**")

    with st.form("single_prediction_form"):
        question1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        question2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Predict Duplicate Status", use_container_width=True, type="primary")

    if submitted:
        if not question1.strip() or not question2.strip():
            st.error("Both question fields are required.")
            return

        with st.spinner(f"Running {selected_model} via {backend_name}..."):
            try:
                start_time = time.time()
                result = get_model_prediction(None, selected_model, question1, question2)
                result["inference_time"] = time.time() - start_time
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        final_pred = result.get("prediction", "Unknown")
        pred_color = "#10B981" if final_pred == "Duplicate" else "#EF4444"
        col1.markdown(
            f"<div class='dashboard-card' style='text-align:center;'>"
            f"<div style='color:{pred_color};font-size:1.2rem;font-weight:700;'>{final_pred}</div>"
            f"<div style='color:#64748B;font-size:0.7rem;text-transform:uppercase;'>Prediction</div></div>",
            unsafe_allow_html=True,
        )

        confidence = result.get("confidence", 0.0)
        col2.metric("Confidence", f"{confidence:.2%}")

        prob_dup = result.get("prob_duplicate", 0.0)
        col3.metric("Duplicate Probability", f"{prob_dup:.2%}")

        latency = result.get("inference_time", 0) * 1000
        col4.metric("Latency", f"{latency:.1f} ms")

        st.caption(
            f"Model: **{result.get('model_label', selected_model)}** | "
            f"Backend: **{result.get('backend', 'N/A')}** | "
            f"Time: {latency:.1f} ms"
        )

        with st.expander("Developer Mode - Execution Proof", expanded=True):
            st.markdown("#### Model Routing Verification")
            st.json(
                {
                    "selected_model": result.get("selected_model", selected_model),
                    "executed_model": result.get("executed_model", "N/A"),
                    "backend": result.get("backend", "N/A"),
                    "artifact_path": result.get("artifact_path", "N/A"),
                    "tokenizer": result.get("tokenizer", "N/A"),
                    "inference_function": result.get("inference_function", "N/A"),
                    "execution_time_ms": result.get("execution_time_ms", 0),
                }
            )

            st.markdown("#### Raw Logits & Softmax")
            raw_logits = result.get("raw_logits")
            softmax_out = result.get("softmax")
            st.json(
                {
                    "raw_logits": raw_logits if raw_logits else "not captured",
                    "softmax": softmax_out if softmax_out else "not captured",
                    "prob_non_duplicate": result.get("prob_non_duplicate", "N/A"),
                    "prob_duplicate": result.get("prob_duplicate", "N/A"),
                    "threshold": result.get("threshold", 0.5),
                }
            )

            st.markdown("#### Label Mapping Trace")
            st.code("Raw logits -> argmax -> class_id -> display_label")
            predicted_class_id = result.get("predicted_class_id")
            label_mapping = result.get("label_mapping")
            final_label = result.get("final_label")
            st.json(
                {
                    "argmax_index": predicted_class_id,
                    "label_mapping": label_mapping if label_mapping else "not available",
                    "final_label": final_label,
                    "confidence": confidence,
                }
            )

            st.markdown("#### Decision Trace")
            st.code(
                f"predicted_label={result.get('predicted_label')} -> "
                f"prediction='{result.get('prediction')}' -> "
                f"confidence={confidence:.4f}"
            )

        st.success(f"Final decision: **{final_pred}** using **{selected_model}**.")
        probability_figure = create_probability_figure(
            prob_duplicate=float(prob_dup), threshold=float(result.get("threshold", 0.5))
        )
        st.pyplot(probability_figure, clear_figure=True)
