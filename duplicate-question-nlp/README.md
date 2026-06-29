# Duplicate Question Detection NLP

Detect duplicate Quora questions using classical NLP features, transformer models, and a production-style Streamlit application.

## Overview

This project follows a five-week NLP roadmap:

- **Week 1:** data collection, cleaning, EDA, and preprocessing
- **Week 2:** TF-IDF, Word2Vec, Sentence-BERT features, and classical ML models
- **Week 3:** DistilBERT fine-tuning and reusable transformer inference
- **Week 4:** threshold tuning, class imbalance handling, and error analysis
- **Week 5:** Streamlit application, dashboarding, batch inference, deployment config, and reusable modules

The Week 5 application now lives in `app.py` and reads the existing project artifacts under `data/`, `models/`, and `results/`.

## Dataset

- **Source:** [`sentence-transformers/quora-duplicates`](https://huggingface.co/datasets/sentence-transformers/quora-duplicates)
- **Primary split used in this project:** `pair-class`
- **Task:** binary classification (`duplicate` vs `non-duplicate`)
- **Rows:** about 404K question pairs

Example:

```text
Question 1: How can I be a good geologist?
Question 2: What should I do to be a great geologist?
Label: duplicate
```

## Week 5 Application Features

The Streamlit app includes:

- Landing page
- Project overview
- Dataset information
- NLP pipeline visualization
- Model information
- Single prediction page
- Confidence score and probability chart
- Batch CSV prediction
- Downloadable prediction results
- Performance dashboard
- Accuracy, precision, recall, F1 score
- Confusion matrix
- ROC curve when available
- Error analysis
- Explainability / Week 4 outputs page
- Model comparison
- Sidebar navigation
- Truthful active-model status with fallback reason reporting
- Artifact-aware cache refresh for model and evaluation outputs
- Loading spinners
- Input validation and error handling
- Deployment-ready configuration

## Automatic Week 4 Fallback Logic

The app automatically resolves the active model:

1. Use `models/week4_improved_model/` when its Hugging Face artifacts are present and load successfully.
2. Otherwise fall back to `models/saved_transformer_model/` from Week 3.
3. Surface the exact fallback reason in the UI instead of silently reporting the wrong active model.

The app now ties its cached model and evaluation state to the underlying artifact files, so adding or updating Week 4 assets causes the UI to refresh to the correct active model and metrics without misleading stale status.

## Refactored App Structure

```text
duplicate-question-nlp/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── src/
│   └── duplicate_question_app/
│       ├── __init__.py
│       ├── artifacts.py
│       ├── config.py
│       ├── inference.py
│       └── visuals.py
├── data/
├── models/
├── notebooks/
└── results/
```

## Existing Project Contents

- `notebooks/data_analysis.ipynb`: Week 1 dataset preparation and EDA
- `notebooks/baseline_model.ipynb`: Week 2 classical baselines and feature engineering
- `notebooks/transformer_model.ipynb`: Week 3 DistilBERT fine-tuning and inference logic
- `notebooks/week4_improvement.ipynb`: Week 4 threshold tuning, weighted loss, and error analysis

## How To Run

From the folder that contains `app.py`:

```bash
cd duplicate-question-nlp/duplicate-question-nlp
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Artifacts (Expected Paths)

The Streamlit application reads artifacts from fixed, repository-relative locations:

- Dataset
  - `data/cleaned_quora.parquet` (preferred) or `data/cleaned_quora.csv`
- Week 3 (Baseline Transformer)
  - Model + tokenizer: `models/saved_transformer_model/` (Hugging Face format)
  - Predictions: `results/transformer_model/transformer_test_predictions.csv`
  - Week 2 vs Week 3 comparison: `results/transformer_model/week2_vs_week3_comparison.csv`
- Week 4 (Improved Transformer)
  - Model + tokenizer: `models/week4_improved_model/` (Hugging Face format)
  - Threshold tuning: `results/week4_improvement/threshold_analysis.csv`
  - Ablation study: `results/week4_improvement/ablation_study.csv`
  - Prediction-level export for evaluation + error analysis: `results/week4_improvement/predictions_week4.csv`
  - Exported figures: `results/week4_improvement/fig*.png`

## App Behavior (Week 3 vs Week 4)

- Inference automatically uses the Week 4 model when `models/week4_improved_model/` contains valid model, config, and tokenizer artifacts; otherwise it falls back to Week 3.
- If Week 4 threshold tuning output is available, the app uses the best-F1 threshold when making decisions.
- The landing page, sidebar, and model information page always report the actually loaded model.
- The Performance Dashboard, Explainability, and Error Analysis pages refresh against the exported Week 4 CSV and plot artifacts and always keep Week 3 results available for comparison.

## Notes About Portability

- The notebooks contain some machine-specific absolute paths in printed outputs, but the Week 5 app uses relative project paths and is portable within this repo layout.
- If model weights are not present on the machine where the app is run, inference pages will show an error until the saved model artifacts are restored.

## Deployment

- Streamlit Community Cloud:
  - Set the app entrypoint to `duplicate-question-nlp/duplicate-question-nlp/app.py`
  - Ensure `requirements.txt` is at `duplicate-question-nlp/duplicate-question-nlp/requirements.txt`
- Local deployment:
  - Run with `python -m streamlit run app.py`
  - Use `.streamlit/config.toml` for theme and server defaults

## Troubleshooting

- `Dataset could not be loaded`
  - Ensure `data/cleaned_quora.parquet` (or `.csv`) exists under the same folder as `app.py`.
- `Model could not be loaded`
  - Ensure `models/week4_improved_model/` or `models/saved_transformer_model/` contains `config.json`, model weights (`model.safetensors` or `pytorch_model.bin`), and tokenizer files.
- App shows Week 3 even though Week 4 files exist
  - Restart Streamlit once if you recently copied new artifacts into the repo. The current app invalidates its cache from file signatures, so refreshed artifacts should be detected automatically on the next run.
- Dashboard pages show empty tables
  - Ensure the corresponding exported CSVs exist under `results/transformer_model/` and `results/week4_improvement/`.

## Core Technologies

- Python
- Pandas
- NumPy
- Scikit-learn
- NLTK
- Gensim
- PyTorch
- Hugging Face Transformers
- Sentence-Transformers
- Streamlit
- Matplotlib
- Seaborn

## References

- [Quora Question Pairs – Kaggle](https://www.kaggle.com/c/quora-question-pairs)
- [sentence-transformers/quora-duplicates – HuggingFace](https://huggingface.co/datasets/sentence-transformers/quora-duplicates)
- [Sentence-BERT Paper](https://arxiv.org/abs/1908.10084)
- [DistilBERT Paper](https://arxiv.org/abs/1910.01108)
