# quora-dupdetect-nlp

> Detecting duplicate questions on Quora using Classical ML and Transformer-based models.

---

## Overview

This project builds an end-to-end NLP pipeline to identify whether two Quora questions share the same intent. It covers everything from classical TF-IDF baselines to fine-tuned Sentence-BERT models, with a working interactive demo.

**Dataset:** [`sentence-transformers/quora-duplicates`](https://huggingface.co/datasets/sentence-transformers/quora-duplicates)  
**Task:** Duplicate Question Detection / Semantic Textual Similarity  
**Language:** English

---

## Dataset

The dataset is the Quora Question Pairs dataset, reformatted into four subsets:

| Subset | Columns | Rows |
|---|---|---|
| `pair-class` | sentence1, sentence2, label | 404k |
| `pair` | anchor, positive | 149k |
| `triplet` | anchor, positive, negative | 102k |
| `triplet-all` | anchor, positive, negative | 2.79M |

**Example:**
```
Question 1: "How can I be a good geologist?"
Question 2: "What should I do to be a great geologist?"
Label:       duplicate ✓
```

---

## Project Structure

```
quora-dupdetect-nlp/
├── data_analysis.ipynb       # EDA & dataset exploration
├── baseline_model.ipynb      # TF-IDF + classical ML
├── transformer_model.ipynb   # Fine-tuned BERT / Sentence-BERT
├── improvement.ipynb         # Ablation & enhancements
├── app.py                    # Streamlit demo
├── requirements.txt
├── results/
│   ├── confusion_matrix.png
│   ├── training_curve.png
│   └── result_table.csv
└── report/
    ├── final_report.docx
    └── presentation.pptx
```

---

## Results

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| TF-IDF + Logistic Regression | - | - | - | - |
| TF-IDF + SVM | - | - | - | - |
| Sentence-BERT (fine-tuned) | - | - | - | - |
| Transformer + Improvement | - | - | - | - |

---

## Setup

```bash
git clone https://github.com/<your-username>/quora-dupdetect-nlp.git
cd quora-dupdetect-nlp
pip install -r requirements.txt
```

**Load the dataset:**
```python
from datasets import load_dataset

# Labeled pairs for classification
ds = load_dataset("sentence-transformers/quora-duplicates", "pair-class")

# Triplets with hard negatives
ds_triplets = load_dataset("sentence-transformers/quora-duplicates", "triplet")
```

---

## Demo

```bash
streamlit run app.py
```

Enter two questions and get a real-time duplicate prediction with a similarity score.

---

## Tech Stack

- **Data:** HuggingFace Datasets, Pandas
- **Classical ML:** Scikit-learn, NLTK, Gensim
- **Deep Learning:** HuggingFace Transformers, Sentence-Transformers, PyTorch
- **Demo:** Streamlit / Gradio
- **Evaluation:** F1, ROC-AUC, Cosine Similarity

---

## References

- [Quora Question Pairs – Kaggle](https://www.kaggle.com/c/quora-question-pairs)
- [sentence-transformers/quora-duplicates – HuggingFace](https://huggingface.co/datasets/sentence-transformers/quora-duplicates)
- [Sentence-BERT Paper](https://arxiv.org/abs/1908.10084)
- [RoBERTa Paper](https://arxiv.org/abs/1907.11692)
