from __future__ import annotations

import time

import streamlit as st

from app.services.runtime import get_runtime_context
from app.utils.constants import get_model_prediction
from duplicate_question_app._visualization.plots import create_probability_figure


def render() -> None:
    st.title("Prediction Page")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Run live inference on individual question pairs with the selected model and Semantic Intelligence Engine.</p>",
        unsafe_allow_html=True,
    )
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    prediction_mode = st.session_state.get("prediction_mode", "fusion")

    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        decision_threshold = metadata.get("decision_threshold", 0.5)
        device = metadata.get("device", "cpu")
    elif metadata:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
        device = metadata.device
    else:
        model_label = selected_model
        decision_threshold = 0.5
        device = "cpu"

    mode_labels = {
        "cross_encoder_only": "🔴 CrossEncoder Only",
        "semantic_only": "🟢 Semantic Intelligence Only",
        "fusion": "🔵 Fusion (Recommended)",
        "cross_encoder_dominant": "🔵 CrossEncoder Dominant",
        "semantic_dominant": "🟢 Semantic Dominant",
        "confidence_weighted": "🟣 Confidence Weighted",
        "adaptive": "🟠 Adaptive",
    }

    col1, col2, col3 = st.columns(3)
    col1.caption(f"Model: **{model_label}**")
    col2.caption(f"Device: **{device}**")
    col3.caption(f"Mode: **{mode_labels.get(prediction_mode, prediction_mode)}**")

    with st.form("single_prediction_form"):
        question1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        question2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Predict Duplicate Status", use_container_width=True, type="primary")

    if submitted:
        if not question1.strip() or not question2.strip():
            st.error("Both question fields are required.")
            return

        with st.spinner(f"Running {model_label} with Semantic Intelligence..."):
            try:
                start_time = time.time()
                result = get_model_prediction(service, selected_model, question1, question2)
                result["inference_time"] = time.time() - start_time
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        fusion_result = result.get("fusion_result", {})

        col1, col2, col3, col4 = st.columns(4)
        final_pred = result.get("final_prediction", result.get("prediction", "Unknown"))

        pred_color = "#10B981" if final_pred == "Duplicate" else "#EF4444"
        col1.markdown(
            f"<div class='dashboard-card' style='text-align:center;'>"
            f"<div style='color:{pred_color};font-size:1.2rem;font-weight:700;'>{final_pred}</div>"
            f"<div style='color:#64748B;font-size:0.7rem;text-transform:uppercase;'>Prediction</div></div>",
            unsafe_allow_html=True,
        )

        fusion_score = fusion_result.get("final_score", result.get("confidence", 0.0))
        col2.metric("Fusion Confidence", f"{fusion_score:.2%}")

        ce_score = fusion_result.get("cross_encoder_score", result.get("prob_duplicate", 0.0))
        col3.metric("CrossEncoder Score", f"{ce_score:.2%}" if ce_score is not None else "N/A")

        semantic_sim = result.get("semantic_similarity", 0.0)
        col4.metric("Semantic Similarity", f"{semantic_sim:.2%}")

        st.caption(
            f"Model: **{result.get('model_label', model_label)}** | "
            f"Mode: **{result.get('prediction_mode', prediction_mode)}** | "
            f"Time: {result.get('inference_time', 0) * 1000:.1f} ms | "
            f"Strategy: **{fusion_result.get('strategy', 'N/A')}**"
        )

        explanation = fusion_result.get("explanation", "")
        if explanation:
            st.info(explanation)

        if fusion_result.get("strategy") == "fusion":
            st.info(
                f"CE={fusion_result.get('cross_encoder_score', 0):.2f} | "
                f"Sem={fusion_result.get('semantic_score', 0):.2f} | "
                f"Final={fusion_result.get('fusion_score', 0):.2f} | "
                f"Conflict Penalty: {fusion_result.get('conflict_penalty_applied', 0):.2f}"
            )

        assessment = result.get("semantic_assessment")
        if assessment:
            with st.expander("Semantic Intelligence Assessment", expanded=False):
                col_a, col_b, col_c = st.columns(3)
                co = assessment.get("concept_overlap", {})
                eo = assessment.get("entity_overlap", {})
                ins = assessment.get("intent_similarity", {})
                rs = assessment.get("relation_similarity", {})
                cs = assessment.get("context_similarity", {})

                col_a.metric("Concept Overlap", f"{co.get('overlap_score', 0):.2%}")
                col_b.metric("Entity Overlap", f"{eo.get('overlap_score', 0):.2%}")
                col_c.metric("Intent Match", f"{ins.get('score', 0):.2%}")

                col_a.metric("Relation Match", f"{rs.get('score', 0):.2%}")
                col_b.metric("Context Similarity", f"{cs.get('score', 0):.2%}")
                col_c.metric("Confidence", f"{assessment.get('confidence', 0):.2%}")

                st.markdown("#### Detected Conflicts")
                conflicts = assessment.get("conflicts", [])
                if conflicts:
                    for c in conflicts:
                        st.warning(
                            f"**{c.get('conflict_type', 'unknown')}**: {c.get('description', '')} (severity: {c.get('severity', 0):.2f})"
                        )
                else:
                    st.success("No conflicts detected.")

                st.markdown("#### Supporting Evidence")
                evidence = assessment.get("supporting_evidence", [])
                for e in evidence:
                    status = e.get("status", "info")
                    msg = e.get("message", "")
                    if status == "match":
                        st.success(f"✓ {msg}")
                    elif status in ("mismatch", "conflict"):
                        st.error(f"✗ {msg}")
                    elif status in ("warning", "low_overlap"):
                        st.warning(f"⚠ {msg}")
                    else:
                        st.info(f"ℹ {msg}")

                with st.expander("Raw Assessment Data", expanded=False):
                    st.json(assessment)
        else:
            st.info("Semantic Intelligence Engine could not produce an assessment for these inputs.")

        if result.get("reason"):
            st.info(f"ℹ️ {result['reason']}")

        if result.get("feature_breakdown"):
            with st.expander("Model Contributions (Ensemble)"):
                for model_name, contrib in result["feature_breakdown"].items():
                    st.write(f"- **{model_name}**: duplicate probability = {contrib.get('prob_dup', 0):.4f}")

        st.success(f"Final decision: **{final_pred}** using **{model_label}**.")
        probability_figure = create_probability_figure(
            prob_duplicate=float(fusion_score), threshold=float(decision_threshold)
        )
        st.pyplot(probability_figure, clear_figure=True)
