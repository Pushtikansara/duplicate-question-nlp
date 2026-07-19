# Duplicate Question Detection NLP

A Streamlit application for detecting duplicate Quora question pairs. The project follows the Summer Internship roadmap from data preparation through classical machine learning baselines, transformer fine-tuning, Week 4 improvements, and a Week 5 demonstration app.

## Roadmap Coverage

- **Week 1:** data cleaning, exploratory analysis, and preprocessing in `notebooks/data_analysis.ipynb`.
- **Week 2:** classical NLP baselines in `notebooks/baseline_model.ipynb`, including TF-IDF + Logistic Regression and TF-IDF + Linear SVM.
- **Week 3:** DistilBERT fine-tuning in `notebooks/transformer_model.ipynb` with saved transformer artifacts and evaluation exports.
- **Week 4:** improved DistilBERT workflow in `notebooks/week4_improvement.ipynb`, including class weighting, threshold tuning, ablation results, ROC comparison, and error analysis.
- **Week 5:** Streamlit app in `app.py` demonstrating the complete project with prediction, batch prediction, dashboards, model comparison, and artifact-aware model loading.

## Week 5 App Pages

- Landing Page
- Project Overview
- Dataset Information
- NLP Pipeline Visualization
- Model Information
- Model Comparison
- Prediction Page
- Batch CSV Prediction
- Performance Dashboard
- Error Analysis
- Explainability

## Model Behavior

The prediction page uses the **Week 4 Improved DistilBERT** model by default when `models/week4_improved_model/` contains loadable Hugging Face artifacts. If Week 4 artifacts are unavailable or fail to load, the app automatically falls back to the Week 3 DistilBERT model in `models/saved_transformer_model/`.

The app does not expose unnecessary model selection on the prediction page. It reports the active model and decision threshold clearly.

## Model Comparison

The dedicated Model Comparison page summarizes:

- TF-IDF + Logistic Regression
- TF-IDF + Linear SVM
- DistilBERT (Week 3)
- Improved DistilBERT (Week 4)

Displayed fields include accuracy, precision, recall, F1 score, ROC AUC when available, training time when available, model size when available, and a short description.

## Project Structure

```text
app/
configs/
docs/
notebooks/
src/duplicate_question_app/
tests/
tools/
pyproject.toml
README.md
```

## Required Artifacts

The app reads project artifacts from repository-relative paths:

- Dataset: `data/cleaned_quora.parquet` or `data/cleaned_quora.csv`
- Week 2 comparison: `outputs/baseline_model/week2_model_comparison.parquet`
- Week 3 model: `models/saved_transformer_model/`
- Week 3 predictions: `outputs/transformer_model/transformer_test_predictions.csv`
- Week 3 comparison: `outputs/transformer_model/week2_vs_week3_comparison.csv`
- Week 4 model: `models/week4_improved_model/`
- Week 4 threshold tuning: `outputs/week4_improvement/threshold_analysis.csv`
- Week 4 ablation: `outputs/week4_improvement/ablation_study.csv`
- Week 4 predictions: `outputs/week4_improvement/predictions_week4.csv`
- Week 4 figures: `outputs/week4_improvement/fig*.png`

## Run Locally

From the repository root:

```bash
pip install -e ".[dev]"
streamlit run app/app.py
```

## Deployment Notes

For Streamlit Community Cloud, set the app entrypoint to:

```text
app/app.py
```

## Troubleshooting

- If the dataset page fails, verify that `data/cleaned_quora.parquet` or `data/cleaned_quora.csv` exists.
- If prediction fails, verify that either Week 4 or Week 3 model artifacts include `config.json`, tokenizer files, and model weights.
- If the dashboard or model comparison page has missing metrics, rerun the corresponding notebook to regenerate the exported files under `outputs/`.
