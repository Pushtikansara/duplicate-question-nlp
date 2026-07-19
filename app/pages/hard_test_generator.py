from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app.hard_test_generator import generate_hard_dataset, save_dataset, print_dataset_stats


def render() -> None:
    st.title("Hard Test Dataset Generator")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate 1000+ extremely difficult question pairs across 13 categories with "
        "abbreviations, synonyms, negation, paraphrases, entity swaps, and contradictions.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        n_pairs = st.slider("Total pairs", 100, 5000, 1000, 100)
        output_path = st.text_input("Output path", "hard_test_dataset.csv")
    with col2:
        include_duplicates = st.checkbox("Include duplicate pairs (paraphrases)", value=True)
        include_non_duplicates = st.checkbox("Include non-duplicate pairs", value=True)

    if st.button("Generate Dataset"):
        with st.spinner("Generating hard test dataset..."):
            try:
                dataset = generate_hard_dataset(
                    n_pairs=n_pairs,
                    include_duplicates=include_duplicates,
                    include_non_duplicates=include_non_duplicates,
                )
                save_dataset(dataset, Path(output_path))
                st.success(f"Generated {len(dataset)} pairs saved to {output_path}")

                stats = print_dataset_stats(dataset)
                st.json(stats)

                st.subheader("Preview")
                preview_df = pd.DataFrame([p.to_dict() for p in dataset[:20]])
                st.dataframe(preview_df, use_container_width=True)

                csv = pd.DataFrame([p.to_dict() for p in dataset]).to_csv(index=False).encode()
                st.download_button("Download CSV", data=csv, file_name="hard_test_dataset.csv", mime="text/csv")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
