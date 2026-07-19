---
name: ml-researcher
description: Use when conducting machine learning research. Covers experiment design, evaluation methodology, paper analysis, and research best practices.
---

# ML Researcher Skill

## Instructions

### Experiment Design

1. **Hypothesis Formulation** - State a clear, falsifiable hypothesis before running experiments. Format: `We hypothesize that [model/method] will outperform [baseline] on [metric] by [effect size] under [conditions].` A good hypothesis specifies the independent variable (what you change), dependent variable (what you measure), and control variables (what stays constant).

2. **Baselines** - Select 2-5 competitive baselines. Include: a simple heuristic or rule-based method, a classical ML approach, the current state-of-the-art, and an ablation of your method (e.g., without your key contribution). Report all baselines in the same experimental setup.

3. **Ablation Studies** - Systematically remove components to measure their contribution. Remove one component at a time. Report performance drop. Design ablations to test specific design decisions, not arbitrary removals. Include negative results (components that hurt performance).

4. **Hyperparameter Sensitivity** - Train and evaluate across a range of hyperparameter values. Report performance as mean +- std over random seeds. Use line plots or heatmaps for visualization. Identify stable regions where performance is robust vs sensitive regions.

5. **Statistical Rigor** - Use multiple random seeds (5-10 minimum). Report mean, standard deviation, and 95% confidence intervals. Apply appropriate statistical tests: paired t-test for comparing two methods, ANOVA for multiple comparisons, Wilcoxon for non-parametric comparisons.

### Evaluation Methodology

1. **Dataset Selection** - Justify dataset choice: Why this dataset? What are its limitations? Is it representative of real-world use? Check for data leakage, label errors, and class imbalance. Use established benchmarks for comparability with prior work.

2. **Train/Validation/Test Split** - Hold out test set for final evaluation only. Use validation set for model selection and hyperparameter tuning. Never let test set influence model development. Report dataset statistics: size per split, class distribution, feature statistics.

3. **Cross-Validation** - Use k-fold cross-validation (k=5 or 10) for smaller datasets. Stratified folds preserve class distribution. Report per-fold results and aggregate statistics. Use nested cross-validation when also tuning hyperparameters.

4. **Metrics Selection** - Choose metrics aligned with the task and real-world requirements. For classification: accuracy (balanced), precision/recall/F1, ROC-AUC, PR-AUC. For regression: MSE, MAE, R^2. For ranking: NDCG, MRR, Recall@K. Avoid reporting only the most favorable metric.

5. **Error Analysis** - Manually examine 50-100 error cases. Categorize error types: label errors, ambiguous examples, missing features, model limitations. Quantify distribution of error types. Error analysis often reveals more insights than aggregate metrics.

6. **Confidence Intervals** - Report 95% confidence intervals using bootstrap (sample with replacement, 1000 iterations). Bootstrap is assumption-free and works for any metric. Visualize with error bars or shaded regions in plots.

### Paper Analysis

1. **Reading Strategy** - First pass: title, abstract, figures, conclusion (5 min). Second pass: introduction, method, experimental setup (30 min). Third pass: full paper with derivations and proofs (2+ hours). Highlight key contributions, assumptions, and limitations.

2. **Critical Evaluation** - For each claim ask: Is the claim supported by evidence? Are the baselines fair? Are the datasets appropriate? Are the statistical tests valid? Are there confounders? Does the method actually outperform simpler baselines?

3. **Reproducibility Assessment** - Check if the paper provides: code, data, hyperparameters, random seeds, hardware specs, training time. Papers without code should be treated with skepticism. Reproducibility checklists (ML Reproducibility Checklist) are good indicators.

4. **Related Work Positioning** - Identify the paper's contribution relative to prior work. Is it incremental (modifying an existing method) or fundamental (new paradigm)? Does it open a new direction or close an existing one? Understanding positioning helps assess significance.

5. **Limitations Recognition** - Every paper has limitations. Common ones: narrow evaluation (1-2 datasets), unrealistic assumptions, computational cost too high for practical use, improvements only on specific data distributions. Identifying limitations is a research skill.

### Research Best Practices

1. **Literature Review** - Systematic process: identify key conferences (NeurIPS, ICML, ICLR, ACL, EMNLP, CVPR, ICCV), use semantic search (Semantic Scholar, Google Scholar), follow citation graphs, track influential authors. Maintain a reading list with annotations.

2. **Experimental Journal** - Keep a detailed log of every experiment: date, hypothesis, configuration, results, observations, next steps. Tools: Weights & Biases, MLflow, or a markdown file. An experiment without a log did not happen.

3. **Code Quality** - Write modular, documented code from day one. Use version control (Git) with meaningful commit messages. Reproducibility requires deterministic code: set seeds, pin dependencies, log all parameters. Your future self will thank you.

4. **Negative Results** - Negative results (hypothesis not supported) are valuable. They prevent others from pursuing the same dead end. Publish negative results in papers, blog posts, or open-source repositories. A well-documented negative result is a contribution.

5. **Collaboration** - Use shared experiment tracking for team research. Document assumptions and design decisions. Code review for all experiments. Regular lab meetings to present work-in-progress. Fresh eyes catch mistakes.

### Research Communication

1. **Paper Writing** - Structure: Title (specific, descriptive), Abstract (problem, method, key results, significance), Introduction (motivation, gap, contribution), Related Work (positioning), Method (detailed, reproducible), Experiments (thorough, fair), Conclusion (summary, limitations, future work).

2. **Figure Design** - Every figure should convey one clear message. Use consistent colors and styles across figures. Label axes clearly with units. Include error bars. Ensure figures are legible when printed in grayscale. Prefer vector graphics (PDF, SVG).

3. **Visualization Best Practices** - Scatter plots for individual data points, line plots for trends, bar charts for comparisons, box plots for distributions, heatmaps for 2D relationships. Avoid 3D plots (obscure information), pie charts (hard to compare), and dual y-axes (misleading).

4. **Presentation Skills** - Tell a story: problem -> gap -> idea -> method -> results -> impact. One message per slide. Use figures, not text walls. Practice timing. Anticipate questions. Prepare backup slides for likely questions. Know your audience.

### Research Ethics

1. **Bias and Fairness** - Evaluate your model across demographic subgroups. Report performance disparities. Consider societal impact. Dataset bias propagates to model bias. Document known biases in your datasets and model.

2. **Environmental Impact** - Report compute budget: GPU hours, estimated CO2 emissions (using ML CO2 Impact calculator). Consider efficiency as a research contribution. Not all problems require the largest models.

3. **Responsible Disclosure** - If your research reveals vulnerabilities or harmful capabilities, follow responsible disclosure practices. Consider dual-use concerns. Engage with ethics review boards when appropriate.

4. **Data Privacy** - Use anonymized data. Do not train on personal data without consent. Consider differential privacy for sensitive applications. Document data provenance and licensing.

## Examples

### Experiment Tracking Setup

```python
import wandb
import numpy as np
from sklearn.model_selection import cross_val_score

config = {
    'model': 'RandomForestClassifier',
    'n_estimators': 100,
    'max_depth': 10,
    'dataset': 'imdb_reviews',
    'embedding': 'tfidf',
    'random_seed': 42,
}

wandb.init(project='sentiment-analysis', config=config)
scores = cross_val_score(model, X, y, cv=5, scoring='f1_macro')
wandb.log({'cv_f1_mean': np.mean(scores), 'cv_f1_std': np.std(scores)})
wandb.log({'confusion_matrix': wandb.plot.confusion_matrix(y_true, y_pred)})
```

### Hypothesis Test for Model Comparison

```python
from scipy import stats

model_a_scores = [0.89, 0.91, 0.88, 0.90, 0.87]
model_b_scores = [0.85, 0.86, 0.84, 0.87, 0.85]

t_stat, p_value = stats.ttest_rel(model_a_scores, model_b_scores)
effect_size = np.mean(model_a_scores) - np.mean(model_b_scores)
ci = stats.t.interval(
    0.95, df=len(model_a_scores)-1,
    loc=effect_size,
    scale=stats.sem(np.array(model_a_scores) - np.array(model_b_scores))
)
print(f'p={p_value:.4f}, effect={effect_size:.3f}, 95% CI={ci}')
```

### Ablation Study Structure

```python
results = {}
for component in ['attention', 'position_encoding', 'layer_norm', 'residual']:
    model = build_model_without(component)
    scores = train_and_evaluate(model, seeds=5)
    results[f'w/o_{component}'] = {'mean': np.mean(scores), 'std': np.std(scores)}

results['full_model'] = {'mean': np.mean(full_scores), 'std': np.std(full_scores)}

# Importance: attention > residual > layer_norm > position_encoding
```

## Best Practices

1. **Pre-register experiments** with hypothesis, method, and analysis plan before running to prevent p-hacking.
2. **Report all metrics**, not just favorable ones; readers need the full picture.
3. **Use the same evaluation protocol** for your method and all baselines; unfair comparisons waste community effort.
4. **Check for data leakage** in preprocessing: feature scaling before split, temporal leakage, duplicate removal.
5. **Visualize results** with multiple perspectives: aggregate metrics, per-class metrics, error distributions, example outputs.
6. **Share code and data** upon publication; unreproducible results are not scientific contributions.
7. **Write as you go** - document method decisions, experimental setup, and observations in real time.
8. **Benchmark on standardized datasets** first, then extend to domain-specific data for generalizability claims.
9. **Engage with the community** through open reviews, workshops, and collaborative projects.
10. **Maintain a research backlog** of ideas, each with a brief description and priority ranking.

## Common Mistakes

1. **p-hacking** - Running many experiments and reporting only significant results without correction.
2. **Unfair baselines** - Comparing against untuned baselines while tuning your method extensively.
3. **Ignoring variance** - Reporting single-run results without error bars, misleading readers about robustness.
4. **Overclaiming** - Claiming generalization from experiments on 1-2 datasets or narrow tasks.
5. **Cherry-picking metrics** - Reporting only the metric where your method excels while hiding others.
6. **No ablation studies** - Not showing which components actually contribute to performance gains.
7. **Data leakage** - Using test data information (implicitly or explicitly) during model development.
8. **Failure to reproduce** - Results that cannot be reproduced by independent researchers due to missing details.
9. **Confirmation bias** - Designing experiments likely to support the hypothesis rather than test it fairly.
10. **Ignoring compute cost** - Proposing methods that are impractical due to computational requirements.

## Libraries

- `scikit-learn` - Baseline models, metrics, cross-validation, preprocessing
- `scipy` - Statistical tests (t-test, ANOVA, Wilcoxon), confidence intervals
- `numpy` / `pandas` - Data manipulation and analysis
- `matplotlib` / `seaborn` - Publication-quality visualizations
- `wandb` - Experiment tracking, visualization, and collaboration
- `mlflow` - Experiment management and model registry
- `transformers` - Pretrained model access and evaluation
- `datasets` - Standardized dataset loading and processing
- `evaluate` - Standardized evaluation metrics from Hugging Face
- `statsmodels` - Advanced statistical modeling and hypothesis testing
- `optuna` / `ray-tune` - Hyperparameter optimization with trial logging
- `papers-with-code` - Benchmark tracking and reproduction

## Design Principles

1. **Science First** - The goal is reliable knowledge, not impressive numbers. Design experiments to test hypotheses, not to win benchmarks.
2. **Reproducibility** - Every result must be reproducible by an independent researcher given the same code, data, and configuration.
3. **Intellectual Honesty** - Report failures, limitations, and negative results alongside successes.
4. **Occam's Razor** - Prefer simpler explanations and methods; complexity must be justified by clear benefits.
5. **Progressive Understanding** - Build understanding incrementally: simple baselines first, then add complexity measured by marginal improvement.
6. **Open Science** - Code, data, and models should be open-source by default unless there are compelling reasons otherwise.
7. **Structured Inquiry** - Research follows the scientific method: hypothesis -> experiment -> analysis -> conclusion -> new hypothesis.

## Coding Standards

1. **Reproducibility setup** - Script header sets all random seeds, device configuration, and deterministic flags.
2. **Configuration management** - All hyperparameters in YAML/JSON config files; never hardcoded in code.
3. **Seed logging** - Log all random seeds used in each experiment for exact reproduction.
4. **Result serialization** - Save all results (metrics, predictions, model weights) in structured format (JSON, numpy, pickle).
5. **Experiment naming** - Use descriptive names: `{method}_{dataset}_{seed}_{date}` for easy identification.
6. **Code organization** - Separate data processing, model definition, training, evaluation, and visualization into distinct modules.
7. **Documentation** - Every function has a docstring describing inputs, outputs, and side effects. Include equation references for novel methods.
8. **Testing** - Unit tests for data preprocessing, metric computation, and model forward pass. Integration tests for full training pipeline on small data.
9. **Version control** - Tag experiment-ready code with Git tags. Branch for each major experiment direction. Keep main branch clean.
10. **Compute logging** - Log GPU/CPU utilization, memory usage, training time per epoch, and total compute cost.
