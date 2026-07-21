# Future Research Directions — ARES v5

**Document Version:** 1.0
**Date:** 2026-07-21
**Scope:** Forward-looking research agenda for ARES version 5 (and beyond), organized by research direction with concrete proposals, expected timelines, and infrastructure requirements.

---

## Table of Contents

1. [Knowledge Graphs Integration](#1-knowledge-graphs-integration)
2. [Multi-Modal Reasoning](#2-multi-modal-reasoning)
3. [LLM Integration](#3-llm-integration)
4. [Retrieval-Augmented Generation (RAG)](#4-retrieval-augmented-generation-rag)
5. [Autonomous Agents](#5-autonomous-agents)
6. [Self-Improving AI](#6-self-improving-ai)
7. [Neuro-Symbolic Reasoning](#7-neuro-symbolic-reasoning)
8. [Causal Reasoning](#8-causal-reasoning)
9. [Priority Matrix & Timeline](#9-priority-matrix--timeline)
10. [Infrastructure Requirements Summary](#10-infrastructure-requirements-summary)

---

## 1. Knowledge Graphs Integration

### Description

Integrate structured world knowledge into the ARES reasoning pipeline via knowledge graphs (KGs). Query external KGs (Wikidata, DBpedia, ConceptNet) for entity resolution, relational reasoning, and common-sense validation of semantic equivalence judgments. A pair like "What is the capital of France?" vs "Is Paris the capital of France?" involves entity-relation triples (Paris, capitalOf, France) that a KG can resolve deterministically while neural models may equivocate.

### Connection to Existing ARES Architecture

The existing `_linguistics/entity.py` engine already performs entity detection using regex patterns and string overlap. This can be upgraded to a knowledge-grounded entity linker (e.g., BLINK, GENRE, or a lightweight spaCy + Wikidata pipeline). The entity linking output would feed into:
- **Ensemble weighting**: Entity-linked pairs receive higher weight from models with strong entity representations
- **Explainability**: Entity resolution facts appear in all 4 explanation levels
- **Agreement analysis**: Entity grounding provides a "ground truth" signal for entity-related disagreements

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| KG-RQ1 | Can KG entity linking improve duplicate detection accuracy for entity-centric questions? | Compare entity-linked vs. regex-based entity features in ensemble | >2% F1 improvement on entity-heavy test subsets (identified via entity density) |
| KG-RQ2 | Can relational KG queries resolve ambiguous entity references that confuse neural models? | Build a KG query module that returns relation overlap scores for question pairs | >5% improvement on "same entity, different relation" pairs |
| KG-RQ3 | How should KG confidence be calibrated against model confidence? | Learn a trust score for KG signals based on KG coverage and query specificity | Well-calibrated KG confidence (ECE < 0.05 on KG-resolvable pairs) |
| KG-RQ4 | Can KG integration reduce ensemble disagreement? | Measure agreement entropy with and without KG features | Significant reduction in agreement entropy (paired t-test, p < 0.01) |
| KG-RQ5 | What KG coverage is needed for meaningful semantic reasoning? | Systematic analysis of how much of the Quora test set is KG-resolvable | Coverage map showing fraction of pairs improved by KG at varying KG sizes |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q1–Q2) | 6 months | Entity linking pipeline (spaCy + Wikidata), KG-aware ensemble weighting, evaluation on entity-heavy pairs |
| Mid (Q3–Q4) | 6 months | Full KG query module (relation extraction + KG path queries), KG-informed calibration |
| Far (Year 2+) | 12+ months | Learned KG query selection (when to query KG and when not to), KG-based explanation generation |

### Required Infrastructure Changes

- **New dependencies:** `spacy` (entity linking), `rdflib` or `SPARQLWrapper` (KG queries), `Wikidata` API access
- **New module:** `_knowledge_graph/` — Entity linker, relation extractor, KG query engine, confidence estimator
- **Config additions:** `configs/knowledge_graph.yaml` — KG endpoints, entity linker model, query timeout, confidence thresholds
- **Model additions:** Entity linker model (cached per session), KG embedding model (optional)
- **Cache expansion:** Entity linking cache (LRU, keyed by text)
- **Evaluation additions:** Entity-heavy subset creation, KG coverage metrics, KG contribution analysis
- **Estimated storage:** 2–5 GB for entity linker model + KG index snapshot

---

## 2. Multi-Modal Reasoning

### Description

Extend ARES beyond text-only duplicate detection to multi-modal inputs. Three concrete directions:

1. **Text + Code**: Detect duplicate programming questions that mix natural language and code snippets — critical for platforms like Stack Overflow
2. **Text + Image**: Detect duplicate questions that include images (e.g., "Why does my code produce this error?" with screenshot)
3. **Text + Table**: Detect duplicate questions about tabular data (e.g., "How do I interpret this regression output?")

### Connection to Existing ARES Architecture

The current inference pipeline processes text pairs exclusively. Multi-modal reasoning requires:
- **New model types**: Multi-modal encoders (CLIP for text+image, CodeBERT for text+code, TAPAS for text+table)
- **Expanded ensemble**: Multi-modal models join the ensemble, with weights conditioned on input modality
- **New linguistic engines**: Code-specific features (syntax similarity, API reference overlap), image-specific features (OCR text, image metadata)
- **Explainability adaptation**: Multi-modal explanations require different formats (image heatmaps, code diffs)

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| MM-RQ1 | Can a unified ensemble handle heterogeneous input modalities gracefully? | Train modality classifiers; learn modality-conditional ensemble weights | No degradation on text-only pairs when multi-modal models are added |
| MM-RQ2 | What cross-modal representations best capture semantic equivalence? | Compare late fusion, early fusion, and hybrid (modality-specific encoders + cross-modal attention) | Best model achieves >80% accuracy on each modality benchmark |
| MM-RQ3 | How should modality-specific calibration be unified? | Learn a modality-conditional calibration mapping | ECE < 0.05 per modality |
| MM-RQ4 | Can multi-modal models improve text-only prediction via shared representations? | Compare multi-modal models fine-tuned on text-only vs. multi-modal data | Multi-modal pre-training improves text-only accuracy by >1% |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q3–Q4) | 6 months | Text+Code support (CodeBERT integration, Stack Overflow dataset), first multi-modal evaluation |
| Mid (Year 2) | 12 months | Text+Image support (CLIP/ALIGN), modality-aware ensemble routing, modality-specific calibration |
| Far (Year 3+) | 12+ months | Full multi-modal framework with arbitrary input types, modality-adaptive explainability |

### Required Infrastructure Changes

- **New dependencies:** `transformers` (multi-modal models already supported), `Pillow` (image processing), `tree-sitter` or `pygments` (code parsing)
- **New modules:** `_modalities/` — Modality classifier, modality-specific preprocessors, modality router
- **Model additions:** CodeBERT, CLIP, TAPAS, modality-specific embedding models (5–10 new models)
- **Dataset additions:** Stack Overflow duplicate questions (code), Quora with images (image), Wikipedia tables (table)
- **Evaluation additions:** Multi-modal benchmarks, modality-stratified metrics, cross-modal transfer analysis
- **Infrastructure:** GPU memory requirements increase by 2–4 GB per multi-modal model loaded
- **Estimated model storage:** 5–15 GB for multi-modal model checkpoints

---

## 3. LLM Integration

### Description

Integrate large language models (GPT-4, Claude, Llama-3, Gemini) into the ARES architecture in three roles:

1. **LLM as a Reasoning Agent**: Replace or augment individual models with LLM-based inference for semantic equivalence. Prompt LLMs with question pairs and ask for duplicate judgment + reasoning.
2. **LLM-Judge for Disagreement Resolution**: When the ensemble shows low agreement, invoke an LLM to analyze the disagreement, examine the evidence from each model, and make a final ruling with explanation.
3. **Prompt-Based Routing**: Use LLM-generated features (not predictions) as additional input to the ensemble weighting mechanism. Ask the LLM "How similar are these questions?" and use the response as a feature.

### Connection to Existing ARES Architecture

LLM integration touches nearly every component:
- **`_models/`**: New model type "llm" with API-based inference, caching, and calibration
- **`_ensemble/`**: LLM as an ensemble member; LLM-judge as a meta-ensemble layer for high-disagreement cases
- **`_linguistics/`**: LLM-based linguistic analysis (beyond regex patterns) — LLM can detect sarcasm, implied negation, pragmatic intent
- **`_explainability/`**: LLM-generated natural language explanations at all 4 levels (currently template-based)
- **`_calibration/`**: LLM confidence is notoriously miscalibrated — requires specialized calibration methods
- **`_evaluation/`**: LLM-as-judge evaluation (using LLMs to evaluate the quality of explanations)

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| LLM-RQ1 | How does LLM-based duplicate detection compare to fine-tuned smaller models in accuracy, latency, and cost? | Systematic comparison of 5+ LLMs vs. existing 11 models on Quora test set | Accuracy vs. latency vs. cost Pareto frontier characterization |
| LLM-RQ2 | When should the LLM-judge be invoked? (What disagreement threshold maximizes accuracy improvement per API call?) | Sweep disagreement thresholds from 0.1 to 0.5; measure accuracy gain per LLM call | Identified optimal threshold with accuracy/cost trade-off curve |
| LLM-RQ3 | Can LLM-generated features improve ensemble weighting beyond hand-crafted linguistic features? | Compare ensemble with hand-crafted features, LLM-generated features, and both | LLM features improve ensemble accuracy by >1% over hand-crafted alone |
| LLM-RQ4 | How should LLM predictions be calibrated for ensemble integration? | Compare temperature scaling, Platt scaling, and binning for LLM logit extraction | ECE < 0.05 for LLM predictions after calibration |
| LLM-RQ5 | Can LLM explanations replace or augment the existing template-based explanation framework? | User study comparing template vs. LLM-generated explanations (accuracy, trust, satisfaction) | LLM explanations preferred in 60%+ of cases on subjective metrics |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q1–Q2) | 6 months | LLM inference wrapper (API-based, cached), LLM-as-ensemble-member evaluation, initial calibration |
| Mid (Q3–Q4) | 6 months | LLM-judge for disagreement resolution, LLM-generated linguistic features, cost-aware routing |
| Far (Year 2+) | 12+ months | Multi-LLM deliberation (multiple LLMs debate), LLM-based explanation generation, on-device LLM (quantized) |

### Required Infrastructure Changes

- **New dependencies:** `openai`, `anthropic`, `transformers` (if using local LLMs), `vLLM` or `llama.cpp` (for local inference)
- **New module:** `_llm/` — LLM client wrapper, prompt templates, response parser, cost tracker, cache (semantic caching of LLM responses)
- **Config additions:** `configs/llm.yaml` — API keys (env-based), model selection, prompt templates per role, cost limits, timeout
- **Infrastructure:** API key management (`.env`), rate limiting, cost tracking dashboard
- **Latency impact:** LLM inference adds 500ms–10s per pair (API-dependent); require async pipeline
- **Cost considerations:** Estimate $0.01–$0.10 per pair for API-based LLM inference; $0 for local models
- **Cache:** Semantic caching of LLM responses (same or similar queries reuse cached responses)

---

## 4. Retrieval-Augmented Generation (RAG)

### Description

Implement RAG to retrieve external evidence for semantic duplicate decisions. When ARES processes a question pair, it retrieves relevant documents, definitions, or similar questions from a knowledge base, and uses this evidence to inform the duplicate judgment. This differs from KG integration (structured facts) by using unstructured text retrieval.

### Connection to Existing ARES Architecture

RAG integrates as a new module that feeds into the ensemble's feature computation:
- **Retrieval**: Given question pair, retrieve top-k relevant passages from a corpus (Wikipedia, Quora archives, documentation)
- **Evidence encoding**: Encode retrieved passages and compute relevance to each question in the pair
- **Feature computation**: Cross-retrieval similarity (do both questions retrieve similar documents?) becomes a feature for ensemble weighting
- **Explainability**: Retrieved evidence is included in explanations ("Both questions reference the same Wikipedia article on photosynthesis")

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| RAG-RQ1 | Can retrieval evidence improve duplicate detection for out-of-domain pairs? | Build retrieval corpus covering Quora topics; evaluate on held-out topic subsets | >3% F1 improvement on low-frequency topic subsets |
| RAG-RQ2 | What retrieval granularity (sentence, paragraph, document) is most useful for semantic equivalence? | Compare sentence-level, passage-level, and document-level retrieval | Passage-level retrieval shows best accuracy-retrieval cost trade-off |
| RAG-RQ3 | How should retrieval relevance be calibrated and combined with model confidence? | Learn a gating mechanism: use retrieval evidence only when model confidence is low | Significant improvement on the low-confidence subset |
| RAG-RQ4 | Can retrieval be used for zero-shot duplicate detection without fine-tuning? | Evaluate frozen LLM + RAG pipeline on Quora without any Quora training | Zero-shot RAG achieves >70% accuracy (baseline: 63% majority class) |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q2–Q3) | 4 months | Basic RAG pipeline (retriever + encoder), Wikipedia corpus indexing, evidence-based feature integration |
| Mid (Q4–Year 2 Q2) | 8 months | Learned retrieve-or-not decisions, multi-corpus retrieval, evidence-based explanation generation |
| Far (Year 2+) | 12+ months | End-to-end trained retrieve-and-decide pipeline, dynamic corpus selection, continual corpus updating |

### Required Infrastructure Changes

- **New dependencies:** `langchain` or `llama-index`, `faiss` (vector store), `sentence-transformers` (already present)
- **New module:** `_retrieval/` — Retriever (BM25, dense), corpus index, evidence encoder, relevance scorer
- **Infrastructure:** Vector database (FAISS index, ~1–10 GB for Wikipedia-sized corpus), document store (text files or SQLite)
- **Dataset additions:** Wikipedia dump, Stack Exchange dump, or custom domain-specific corpora (5–10 GB disk)
- **Latency impact:** Retrieval adds 50–200ms per query (with FAISS); evidence processing adds 100–500ms
- **Config additions:** `configs/retrieval.yaml` — Corpus path, retrieval method, top-k, relevance threshold
- **Cache:** Query-result cache (semantic similarity-based) to avoid redundant retrievals

---

## 5. Autonomous Agents

### Description

Transform ARES from a passive prediction system into an autonomous agent that actively improves its own performance:

1. **Self-Improving Models**: The system detects its own errors, diagnoses failure modes, and adjusts its ensemble weights or triggers re-training
2. **Active Learning**: The system identifies informative pairs (high disagreement, low confidence, novel entities) and requests labels from a human or oracle
3. **Query Generation**: For ambiguous pairs, the system generates clarifying questions to disambiguate intent before making a prediction

### Connection to Existing ARES Architecture

The autonomous agent layer builds on the existing agreement analysis and evaluation infrastructure:
- **`_ensemble/agreement.py`**: Agreement entropy becomes the primary signal for identifying uncertain cases
- **`_evaluation/error_analysis.py`**: Error categories define the action space (which corrective action to take)
- **`_explainability/`**: Explanations become the basis for understanding _why_ the system is uncertain
- **`_training/`**: Active learning loop selects training examples; self-improvement loop triggers re-training

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| AA-RQ1 | Can the system learn to predict its own errors before making them? | Train a meta-classifier on features (agreement entropy, confidence, linguistic features) to predict prediction correctness | AUC > 0.8 for error prediction; enables selective abstention |
| AA-RQ2 | What is the optimal active learning strategy for semantic duplicate detection? | Compare uncertainty sampling, disagreement sampling, diversity sampling, and hybrid strategies in a simulated labeling budget | 50% labeling budget to reach 95% of full-data accuracy |
| AA-RQ3 | Can the system generate useful clarifying questions for ambiguous pairs? | Train a question generation model (T5 or LLM) to generate disambiguating questions based on the decision trace | Human evaluation: 70%+ of generated questions are relevant and useful |
| AA-RQ4 | Can the system autonomously improve its ensemble weights over time? | Implement online weight learning (exponential-weight algorithm for exploration and exploitation) with feedback from downstream tasks | Convergence to near-optimal weights within 1,000 online examples |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q2–Q4) | 8 months | Error prediction module, simulated active learning (off-line evaluation), query generation prototype |
| Mid (Year 2) | 12 months | Online active learning loop (human-in-the-loop), ensemble weight adaptation, autonomous error diagnosis dashboard |
| Far (Year 3) | 12+ months | Fully autonomous agent: self-diagnose, self-improve, self-query; minimal human intervention for routine improvements |

### Required Infrastructure Changes

- **New module:** `_agents/` — Error predictor, active learning selector, query generator, weight optimizer, improvement tracker
- **Infrastructure:** Human-in-the-loop interface (annotator queue, labeling dashboard), online learning framework
- **Config additions:** `configs/agents.yaml` — Learning strategy, labeling budget, improvement triggers, query generation parameters
- **Data storage:** Error prediction training data, active learning history, weight adaptation logs
- **Evaluation additions:** Simulated labeling budget experiments, autonomous improvement rate metrics, human effort reduction measurement
- **Ethical considerations:** Active learning reduces but does not eliminate the need for human annotation; clear annotation instructions needed

---

## 6. Self-Improving AI

### Description

Design ARES with continuous self-improvement capabilities that operate without human intervention:

1. **Online Learning from Mistakes**: When the system discovers it made an error (e.g., through explicit user feedback, downstream task validation, or consistency checks), it updates its models or weights
2. **Automatic Calibration Updates**: Monitor calibration drift over time and automatically recalibrate when ECE exceeds a threshold
3. **Drift Adaptation**: Detect distribution shift in incoming queries and adapt ensemble weights or trigger re-training
4. **Consistency Self-Training**: Use high-confidence predictions on unlabeled data as pseudo-labels for self-training

### Connection to Existing ARES Architecture

Self-improvement mechanisms directly extend the existing evaluation and monitoring pipeline:
- **`_calibration/v1.py` and `v2.py`**: Already implement calibration; add automatic recalibration triggers
- **`_evaluation/metrics.py`**: Add drift metrics (PSI, distribution comparison)
- **`_ensemble/`**: Add online weight learning
- **`_training/classifier_head.py`**: Add online fine-tuning capability (lightweight head updates without full re-training)

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| SI-RQ1 | What is the best online learning algorithm for ensemble weight adaptation? | Compare Hedge algorithm, exponentiated gradient, online gradient descent, and Bayesian online learning | Sub-linear regret compared to best fixed weights on held-out stream |
| SI-RQ2 | How can the system distinguish distribution shift from label noise in feedback? | Design a probabilistic model that attributes errors to shift vs. noise | Accurate attribution (AUC > 0.9) on synthetic shift vs. noise detection |
| SI-RQ3 | Does self-training with pseudo-labels improve or degrade accuracy over time? | Longitudinal study: apply self-training over 6 months of simulated streaming data | Accuracy does not degrade below initial baseline (no catastrophic forgetting) |
| SI-RQ4 | What triggers should initiate automatic recalibration? | Sweep ECE thresholds, Brier score changes, and time-window-based triggers | Optimal trigger achieves <0.01 average ECE over stream with minimal recalibrations |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q3–Q4) | 6 months | Off-line evaluation of online learning strategies (simulated stream), automatic recalibration trigger system |
| Mid (Year 2) | 12 months | Online ensemble weight adaptation with regret tracking, self-training pipeline (with quality filtering) |
| Far (Year 3+) | 12+ months | Fully autonomous self-improvement loop: drift detection → diagnosis → adaptation → monitoring; minimal human oversight |

### Required Infrastructure Changes

- **New module:** `_self_improve/` — Online learner, drift detector, auto-calibrator, self-training supervisor, performance tracker
- **Infrastructure:** Streaming data pipeline (simulated for development), feedback collection mechanism, versioned model snapshots
- **Config additions:** `configs/self_improve.yaml` — Learning rate, drift detection window, recalibration ECE threshold, self-training confidence threshold
- **Data storage:** Performance history (time-series database), model version snapshots, drift events log
- **Safety-critical design:** Automatic rollback if self-improvement degrades performance; human override for critical changes
- **Testing additions:** Simulation framework for evaluating self-improvement strategies without live deployment

---

## 7. Neuro-Symbolic Reasoning

### Description

Move beyond the current ensemble approach (which combines neural models with symbolic linguistic features but keeps them separate) toward a tighter integration of neural and symbolic reasoning:

1. **Symbolic Feature Injection**: Inject symbolic features (entity linking, negation scope, semantic role labels) as differentiable inputs to neural models during both training and inference
2. **Neural-Guided Symbolic Reasoning**: Use neural models to guide symbolic reasoning (e.g., neural selection of which linguistic rules to apply)
3. **Differentiable Logic**: Implement differentiable fuzzy logic operators that combine neural and symbolic representations in a unified differentiable graph
4. **Rule-Based Regularization**: Use symbolic rules to regularize neural training (e.g., consistency losses: if entity and negation match, the prediction should favor non-duplicate)

### Connection to Existing ARES Architecture

ARES already has the foundation for neuro-symbolic reasoning:
- **Linguistic engines** (`_linguistics/`): Provide symbolic features
- **Ensemble** (`_ensemble/`): Combines neural and symbolic signals, but as separate parallel paths
- **Explainability** (`_explainability/`): Already traces both neural and symbolic reasoning paths

The upgrade is to make the integration tighter and differentiable:
- Symbolic features are not just ensemble weight inputs but also condition the neural model representations
- Neural models learn to use symbolic features, not just be weighted by them
- A differentiable logic layer enables end-to-end training of the combined system

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| NS-RQ1 | Can symbolic features improve neural representations via feature-wise conditioning? | Implement FiLM (Feature-wise Linear Modulation) layers that condition transformer hidden states on symbolic features | >1% accuracy improvement over post-hoc feature combination (current approach) |
| NS-RQ2 | Can differentiable fuzzy logic improve calibration for linguistically clear cases? | Implement an LTN (Logic Tensor Network) layer that enforces logical consistency | ECE improvement >0.02 on linguistically unambiguous subsets |
| NS-RQ3 | What is the optimal architecture for combining neural representations with symbolic features? | Compare late fusion, early fusion, FiLM conditioning, and graph-based integration | Systematic architecture comparison identifies best fusion strategy |
| NS-RQ4 | Can neural models learn to correct or extend the symbolic rule set? | Train a neural model to predict when each symbolic rule applies and when it should be overridden | Neural override improves accuracy on rule-violating edge cases by >5% |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Q4–Year 2 Q2) | 8 months | Feature-wise conditioning integration (FiLM layers in transformer), ablation study of fusion strategies |
| Mid (Year 2 Q3–Q4) | 6 months | Differentiable fuzzy logic prototype (LTN-based), consistency loss training, evaluation on linguistically challenged subsets |
| Far (Year 3) | 12+ months | Full neuro-symbolic architecture: end-to-end differentiable, learns symbolic rules from data, provides symbolic explanations |

### Required Infrastructure Changes

- **New dependencies:** `ltn` or `logic_tensor_networks` (if available), `torch` (remains core framework)
- **New modules:** Feature conditioning layers (FiLM, gated residual networks), differentiable logic operators (AND, OR, NOT, IMPLIES with fuzzy semantics), consistency loss functions
- **Model modifications:** Transformer models need modification to accept conditioning vectors (minor architecture change)
- **Training modifications:** Consistency loss needs careful weighting to not overwhelm primary task loss
- **Evaluation additions:** Linguistically defined evaluation subsets (e.g., "negation pairs" with ground-truth symbolic labels), neuro-symbolic integration metrics
- **GPU requirements:** Additional memory for differentiable logic computation (estimated +10–20% per model)

---

## 8. Causal Reasoning

### Description

Introduce causal reasoning capabilities to ARES, moving beyond correlation-based prediction to intervention-based understanding:

1. **Intervention-Based Analysis**: For a given prediction, ask counterfactual questions: "Would the prediction change if the negation were removed?" or "Would the prediction change if the entity were replaced?"
2. **Causal Feature Attribution**: Attribute predictions to causal features (features whose intervention changes the prediction) rather than correlational features (features that happen to co-occur)
3. **Causal Structure Learning**: Learn a causal graph of how linguistic features, model outputs, and ground truth relate to each other
4. **Counterfactual Explanation**: Generate explanations in counterfactual form: "The pair was classified as duplicate because both use 'Python'; if 'Python' were replaced with 'Java', the prediction would change to non-duplicate"

### Connection to Existing ARES Architecture

Causal reasoning is a natural extension of the existing explainability framework:
- **`_explainability/text.py`**: Level 4 Comprehensive explanations already include counterfactuals (hand-crafted). Causal methods would automate and ground this.
- **`_explainability/trace.py`**: Decision traces already record all the information needed for intervention analysis. Adding causal inference would extract causal, not just correlational, relationships.
- **`_ensemble/`**: Understanding the causal structure of ensemble predictions enables more principled ensemble design.
- **`_linguistics/`**: Causal analysis can reveal which linguistic features actually _cause_ prediction changes vs. merely correlate with them.

### Research Questions

| RQ | Question | Methodology | Success Criterion |
|---|---|---|---|
| CAU-RQ1 | Can causal feature attribution improve the quality of generated explanations? | User study comparing correlational vs. causal explanations (comprehension, actionability, trust) | Causal explanations rated significantly higher on all dimensions |
| CAU-RQ2 | What is the causal structure of the ARES ensemble? | Learn a causal DAG over variables (linguistic features, model predictions, ensemble weights, ground truth) | The learned causal graph is consistent with known dependencies and reveals novel insights |
| CAU-RQ3 | Can counterfactual explanations be generated efficiently for real-time use? | Compare amortized counterfactual generation (trained generator) vs. per-query optimization | Amortized generation achieves <100ms latency vs. >1s for per-query methods |
| CAU-RQ4 | Does causal understanding improve model robustness to spurious correlations? | Identify spurious correlations via causal discovery; train debiased models using causal regularization | Improved OOD performance: >2% on distribution-shifted evaluation sets |
| CAU-RQ5 | Can intervention-based analysis identify model limitations that correlation-based analysis misses? | Systematic comparison of insights from causal vs. correlational error analysis | Causal analysis reveals at least 3 novel failure modes not identified by correlational analysis |

### Expected Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Near (Year 2 Q1–Q2) | 6 months | Causal structure learning over existing system (discovery phase), counterfactual explanation prototype for Level 4 |
| Mid (Year 2 Q3–Q4) | 6 months | Automated counterfactual generation framework, causal attribution integrated into explainability pipeline |
| Far (Year 3) | 12+ months | Causal debiasing (training with causal regularization), full causal graph with intervention-based evaluation, real-time counterfactual explanations |

### Required Infrastructure Changes

- **New dependencies:** `causalnex` or `dowhy` or `causalml` (causal inference libraries)
- **New module:** `_causal/` — Causal graph learner, counterfactual generator, intervention simulator, causal attribution scorer
- **Infrastructure:** Simulation environment for intervention testing (editing text features at scale), causal graph visualization (D3.js or pyvis for Streamlit)
- **Evaluation additions:** Counterfactual quality metrics (validity, minimality, fluency), causal discovery accuracy (if ground truth available), user study framework
- **Config additions:** `configs/causal.yaml` — Causal discovery method, intervention budget, counterfactual generation strategy
- **Compute requirements:** Causal discovery on full system requires substantial compute (iterative graph search across 20+ variables); parallelizable

---

## 9. Priority Matrix & Timeline

### Integration Difficulty vs. Expected Impact

| Direction | Integration Difficulty | Expected Impact | Priority | Timeline |
|---|---|---|---|---|
| LLM Integration | Medium | Very High | **P0** | Near |
| Autonomous Agents | High | High | **P1** | Mid |
| RAG | Medium | High | **P1** | Near–Mid |
| Neuro-Symbolic | High | High | **P1** | Mid–Far |
| Knowledge Graphs | Medium | Medium | **P2** | Near–Mid |
| Causal Reasoning | Very High | Medium-High | **P2** | Mid–Far |
| Self-Improving AI | High | Medium-High | **P2** | Mid–Far |
| Multi-Modal | High | Medium | **P3** | Far |

### Dependency Graph

```
Year 1 (Near)                       Year 2 (Mid)                    Year 3 (Far)
┌────────────────┐           ┌────────────────────┐         ┌──────────────────────────┐
│ LLM Integration │──────────▶│ Autonomous Agents   │────────▶│ Self-Improving AI        │
│ (foundation)    │           │ (uses LLM as judge) │         │ (autonomous loop)         │
└────────────────┘           └────────────────────┘         └──────────────────────────┘
        │                             │                                  │
        ▼                             ▼                                  ▼
┌────────────────┐           ┌────────────────────┐         ┌──────────────────────────┐
│ RAG            │──────────▶│ Knowledge Graphs    │────────▶│ Neuro-Symbolic Reasoning │
│ (retrieval)    │           │ (structured + text) │         │ (differentiable logic)    │
└────────────────┘           └────────────────────┘         └──────────────────────────┘
                                                                    │
        ┌──────────────────────────────────────────────────────────┘
        ▼
┌────────────────────┐
│ Causal Reasoning   │
│ (intervention-based)│
└────────────────────┘

┌────────────────┐
│ Multi-Modal     │  (Independent track, connects at Ensemble layer)
└────────────────┘
```

### Resource Allocation

| Year | Primary Focus | Researchers Needed | Compute Budget | Publication Target |
|---|---|---|---|---|
| Year 1 | LLM integration, RAG, KG | 2–3 NLP researchers, 1 ML engineer | $10–20K (API costs + GPU credits) | 2 workshop + 2 conference |
| Year 2 | Autonomous agents, neuro-symbolic, causal | 3–4 NLP researchers, 1 ML engineer, 1 cognitive scientist | $30–50K (GPU cluster + API costs) | 2 conference + 1 journal |
| Year 3 | Self-improving AI, multi-modal, synthesis | 4–5 researchers (interdisciplinary) | $50–100K (large GPU cluster + storage) | 2 conference + 2 journal |

---

## 10. Infrastructure Requirements Summary

### New Modules

| Module | Purpose | Priority | Lines of Code (Est.) |
|---|---|---|---|
| `_knowledge_graph/` | Entity linking, KG queries, relational reasoning | P2 | 3,000–5,000 |
| `_modalities/` | Modality classification, modal-specific preprocessing | P3 | 2,000–4,000 |
| `_llm/` | LLM client, prompt management, cost tracking | P0 | 2,000–3,000 |
| `_retrieval/` | Dense/sparse retrieval, corpus indexing, evidence scoring | P1 | 3,000–5,000 |
| `_agents/` | Active learning, error prediction, query generation | P1 | 4,000–6,000 |
| `_self_improve/` | Online learning, drift detection, auto-calibration | P2 | 3,000–5,000 |
| `_neuro_symbolic/` | Differentiable logic, feature conditioning, consistency loss | P1 | 4,000–6,000 |
| `_causal/` | Causal discovery, counterfactual generation, attribution | P2 | 4,000–6,000 |

### Storage Requirements

| Component | Size | Type | Priority |
|---|---|---|---|
| LLM model weights (quantized, local) | 4–8 GB | Model storage | P0 |
| RAG corpus (Wikipedia subset) | 5–10 GB | Text corpus | P1 |
| Knowledge graph index (Wikidata subset) | 2–5 GB | KG index | P2 |
| Multi-modal model weights | 5–15 GB | Model storage | P3 |
| Experiment tracking database | 10–100 GB (growing) | Metrics DB | P1 |
| FAISS vector index (for RAG) | 1–10 GB | Vector index | P1 |
| Causal discovery results | 1–5 GB | Analysis output | P2 |
| Training data (augmented) | 5–20 GB | Dataset | P1 |
| Streaming simulation logs | 10–50 GB/year | Logs | P2 |

### Compute Requirements

| Component | CPU | GPU | RAM | Priority |
|---|---|---|---|---|
| LLM inference (API-based) | Minimal | Not needed | Minimal | P0 |
| LLM inference (local, 7B quantized) | 8+ cores | 8–16 GB VRAM | 32 GB | P0 |
| RAG indexing | 4+ cores | Optional (4 GB) | 16 GB | P1 |
| Neuro-symbolic training | 8+ cores | 16–24 GB VRAM | 32 GB | P1 |
| Causal discovery | 16+ cores | Optional | 64 GB | P2 |
| Multi-modal training | 16+ cores | 24–48 GB VRAM | 64 GB | P3 |
| Online learning simulation | 8+ cores | Optional (4 GB) | 16 GB | P2 |
| DRAM for serving all models + LLM | 8+ cores | 16–24 GB VRAM | 32 GB | P1 |

### Recommended Development Environment

```
Phase 1 (Year 1):
  - Development: 1x GPU workstation (RTX 4090, 24 GB VRAM, 64 GB RAM)
  - API access: OpenAI / Anthropic API keys
  - Storage: 100 GB SSD for models, data, and logs
  - Cost: ~$5K hardware + $1K/month API

Phase 2 (Year 2):
  - Development: 2x GPU workstation (RTX 4090 or A6000)
  - Cloud compute: Lambda Labs / RunPod for large experiments ($2–5K/month)
  - Storage: 500 GB SSD + 5 TB HDD (corpora, logs, experiment data)
  - Experiment tracking: Self-hosted MLflow server (8 GB RAM, 100 GB)

Phase 3 (Year 3):
  - Development: GPU cluster (4–8x A100 or H100, $10–20K/month)
  - On-premise or cloud: Determined by cost optimization
  - Storage: 10+ TB (multi-modal data, large corpora, experiment DB)
  - Collaboration infrastructure: Shared experiment server, model registry
```

---

## Visual Summary

```
ARES v5 Research Architecture
══════════════════════════════

                    ┌─────────────────────────────┐
                    │      Causal Reasoning        │
                    │   (intervention, counter-    │
                    │    factual, causal graph)    │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────┴───────────────┐
                    │    Neuro-Symbolic Core       │
                    │  (diff. logic + neural repr) │
                    └─────────────┬───────────────┘
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     │                            │                            │
     ▼                            ▼                            ▼
┌────────────┐           ┌────────────────┐           ┌──────────────┐
│ Knowledge  │           │   ARES Core    │           │  Multi-Modal │
│ Graphs     │◄─────────▶│ (existing v4)  │◄─────────▶│  Encoders    │
│ (Wikidata) │           │ 11 models      │           │ (Code, Image,│
└────────────┘           │ 5 ling engines │           │  Table)      │
                         │ 4 explanation  │           └──────────────┘
     ┌──────────────────▶│ levels         │◄───────────┐
     │                   │ 2 calibration  │            │
     │                   └───────┬────────┘            │
     │                           │                     │
     ▼                           ▼                     ▼
┌────────────┐           ┌────────────────┐           ┌──────────────┐
│ RAG        │           │  LLM Layer     │           │ Autonomous   │
│ (retrieval │           │ (reasoner,     │           │ Agents       │
│  + evidence)│          │  judge, router)│           │ (active lrn, │
└────────────┘           └────────────────┘           │ self-improve)│
                                                       └──────────────┘
                                               ┌──────────────┐
                                               │ Self-Improving│
                                               │ AI (online    │
                                               │  learning)    │
                                               └──────────────┘
```

---

*This document is a living research agenda. Directions should be revisited annually based on published results, community trends, and available resources.*
