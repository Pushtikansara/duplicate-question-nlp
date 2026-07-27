# Semantic Audit — Phase 10.6.6

## Abbreviation Expansion

The `normalize_question()` function in `src/duplicate_question_app/_preprocessing/text.py` now uses `expand_abbrevs=True` for ALL backends.

### Previous Bug
The transformer inference path used `expand_abbrevs=False`, which meant:
- "what is ai" stayed as "what is ai"
- "what is artificial intelligence" stayed as "what is artificial intelligence"
- Embeddings would not match these as the same concept
- Result: Non-Duplicate (100% confidence) — clearly wrong

### Fix
All backends now call `normalize_question(expand_abbrevs=True, fix_typos=True)`:
- "what is ai" → "what is ai (artificial intelligence)"
- "what is artificial intelligence" → "what is artificial intelligence"
- Now both questions contain "artificial intelligence" tokens → Duplicate

### Abbreviations Supported
AI, ML, NLP, DL, CV, NLG, NLU, OCR, ASR, GAN, RNN, CNN, LSTM, GRU, SVM, KNN, PCA, SGD, ReLU, BERT, GPT, CPU, GPU, RAM, SSD, HDD, USB, API, SDK, IDE, SQL, NoSQL, HTML, CSS, JS, JSON, XML, YAML, HTTP, HTTPS, FTP, TCP, UDP, IP, DNS, DBMS, RDBMS, CLI, GUI, UI, UX, AJAX, REST, CRUD, ORM, OOP, BDA, TDD, CI, CD, QA, MLE, MAP, EM, MCMC, ODE, PDE, USA, UK, EU, UN, OS, DB

### Semantic Regression Cases

| Question 1 | Question 2 | Expected | Actual (all models) |
|---|---|---|---|
| what is ai | what is ai | Duplicate | Duplicate |
| what is ai | what is artificial intelligence | Duplicate | Duplicate |
| dbms | database management system | Duplicate | Duplicate |
| ml | machine learning | Duplicate | Duplicate |
| cnn | convolutional neural network | Duplicate | Duplicate |
| nlp | natural language processing | Duplicate | Duplicate |
| cat | dog | Non-Duplicate | Non-Duplicate |
| python list | python tuple | Non-Duplicate | Non-Duplicate |
| hello | hello | Duplicate | Duplicate |
| oop | object oriented programming | Duplicate | Duplicate |
| lstm | long short term memory | Duplicate | Duplicate |
| bert | bidirectional encoder representations from transformers | Duplicate | Duplicate |
| gpt | generative pretrained transformer | Duplicate | Duplicate |

## Label Mapping Audit

All backends use consistent label mapping: `{0: "Non-Duplicate", 1: "Duplicate"}`

Trace: `raw_logits → softmax → argmax → class_id → label_mapping[class_id] → final_label`

This is verified in every `BackendResult` via:
- `raw_logits`: raw model output
- `softmax`: probabilities after softmax
- `predicted_class_id`: argmax of softmax
- `label_mapping`: dict mapping ID → label string
- `final_label`: `label_mapping[predicted_class_id]`
- `predicted_label`: integer 0 or 1
- `prediction`: "Duplicate" or "Non-Duplicate"
