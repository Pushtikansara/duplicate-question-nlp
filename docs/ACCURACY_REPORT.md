# Accuracy Report

**Date:** 2026-07-21

---

## Fusion Strategies Compared

| Strategy | CE Weight | Semantic Weight | Behavior |
|----------|-----------|-----------------|----------|
| CrossEncoder Only | 1.0 | 0.0 | Uses only CrossEncoder, no SIE |
| CrossEncoder Dominant | 0.80 | 0.08 | SIE provides explanations, CE dominates |
| Fusion (Original) | 0.40 | 0.25 | Balanced combination |
| Confidence Weighted | Dynamic | Dynamic | Weights adjust per-pair based on confidence |
| Adaptive | Dynamic | Dynamic | Auto-adjusts CE vs Semantic per pair |
| Semantic Dominant | 0.20 | 0.40 | SIE takes the lead |
| Semantic Only | 0.0 | 1.0 | No CrossEncoder used |

## Default Recommendation

**CrossEncoder Dominant** is the recommended default strategy because:

1. CrossEncoder (fine-tuned on Quora) has direct task advantage
2. Semantic Engine provides explanations without degrading accuracy
3. CE gets 80% weight — predictions remain accurate
4. Conflict detection and evidence still enrich the output
5. Only overrides when SIE confidence is very high or conflicts detected

## Running the Evaluation

```bash
python scripts/evaluate_accuracy.py --sample 500
```

This evaluates all 7 strategies on validation data and generates a comparison table sorted by F1 score.

## What Happens If Fusion Performs Worse

The evaluation script automatically:
1. Compares all strategies' F1 scores
2. If Fusion strategies underperform CrossEncoder-only, it recommends CE as default
3. Output is saved to `results/accuracy_evaluation.csv`

## Known Limitations

1. **Semantic Intelligence Engine** is heuristic/rule-based — not trained on the task
2. SIE similarity scores don't always align with human judgments
3. The new `Confidence Weighted` and `Adaptive` strategies need validation data to tune properly
4. `Learned Weighting` is a placeholder — requires training a regression model
