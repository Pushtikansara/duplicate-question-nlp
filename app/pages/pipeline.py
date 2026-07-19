from __future__ import annotations

import streamlit as st

from duplicate_question_app.visuals import create_pipeline_figure


def render() -> None:
    st.title("NLP Pipeline Visualization")
    st.write("This visualization shows how the project evolved from raw data to a deployed prediction interface.")
    pipeline_figure = create_pipeline_figure()
    st.pyplot(pipeline_figure, clear_figure=True)
    with st.expander("Pipeline Details", expanded=True):
        st.markdown("""- **Input layer:** two user questions
- **Tokenizer:** DistilBERT pair tokenization with max_length=128
- **Classifier:** fine-tuned sequence classification head
- **Post-processing:** probability computation, thresholding, confidence scoring
- **Phase 2:** Additional embedding models and ensemble""")
