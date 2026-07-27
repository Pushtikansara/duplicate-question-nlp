# Regression Results — Phase 10.6.6

## Semantic Regression Test Suite

**File:** `tests/regression/test_semantic_regression.py`

### Test Cases
| Question 1 | Question 2 | Expected Label | Expected Prediction | Category |
|---|---|---|---|---|
| what is ai | what is ai | 1 | Duplicate | identical text |
| what is ai | what is artificial intelligence | 1 | Duplicate | abbreviation expansion |
| dbms | database management system | 1 | Duplicate | abbreviation expansion |
| ml | machine learning | 1 | Duplicate | abbreviation expansion |
| cnn | convolutional neural network | 1 | Duplicate | abbreviation expansion |
| nlp | natural language processing | 1 | Duplicate | abbreviation expansion |
| cat | dog | 0 | Non-Duplicate | different concepts |
| python list | python tuple | 0 | Non-Duplicate | different python types |
| hello | hello | 1 | Duplicate | identical text |
| what is nlp | natural language processing | 1 | Duplicate | abbreviation vs full form |
| oop | object oriented programming | 1 | Duplicate | abbreviation expansion |
| lstm | long short term memory | 1 | Duplicate | abbreviation expansion |
| bert | bidirectional encoder representations from transformers | 1 | Duplicate | abbreviation expansion |
| gpt | generative pretrained transformer | 1 | Duplicate | abbreviation expansion |
| what is ai | what is ml | 0 | Non-Duplicate | different topics |

### Additional Tests
- `test_selected_model_equals_executed_model()`: Verifies that the selected model name matches the executed model name for all registered models
- `test_developer_proof_fields_present()`: Verifies backend, raw_logits, softmax, predicted_class_id, label_mapping, final_label are all present

## Model Comparison Benchmark

**File:** `tests/regression/test_model_comparison.py`

### Metrics Collected
- Accuracy
- Precision
- Recall
- F1 Score
- Average Latency (ms)
- Average Confidence

### Ground Truth
Uses the 15 semantic regression cases as ground truth.
All models are evaluated on the same test set.

## Running Tests

```bash
# Run semantic regression tests
python -m pytest tests/regression/test_semantic_regression.py -v

# Run model comparison benchmark
python -m pytest tests/regression/test_model_comparison.py -v -s

# Run all regression tests
python -m pytest tests/regression/ -v
```
