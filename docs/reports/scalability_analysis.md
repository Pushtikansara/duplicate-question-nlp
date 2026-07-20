# Scalability Analysis — ARES Foundation

**Version:** 1.0
**Date:** 2026-07-20

---

## 1. Scalability Score: 4.2/10

**Interpretation:** The codebase is **not designed for scale**. It works well for single-user, single-process usage but would fail under load, with large datasets, or in multi-user scenarios.

---

## 2. Scalability Dimensions

### 2.1 Inference Throughput — Score: 3/10

**Current capability:**
- Single prediction: ~200-500ms (varies by model)
- Batch prediction: ~50-100ms per pair (with batching)
- Ensemble: ~2-5s (loads all models)

**Limitations:**
- Streamlit is single-threaded — one prediction at a time
- Ensemble loads ALL models into memory simultaneously
- No request queuing — concurrent users compete for the same process
- No GPU sharing — single GPU, first-come-first-served

**Scaling bottlenecks:**
```
Bottleneck 1: Model loading (1-10s, blocking)
Bottleneck 2: Transformer inference (500ms, CPU-bound)
Bottleneck 3: Ensemble aggregation (2-5s, loads all models)
Bottleneck 4: Streamlit single-threaded (1 request at a time)
```

**Theoretical max throughput (single instance):**
- Single model: ~2-5 requests/second
- Ensemble: ~0.2-0.5 requests/second
- Batch (64 pairs): ~10-20 pairs/second

### 2.2 Data Volume — Score: 5/10

**Current dataset:** ~404K pairs (323K train, 40K val, 40K test)

**Can handle:**
- Loading full dataset in memory (pandas DataFrame)
- TF-IDF vectorization of full dataset
- Embedding computation for full dataset

**Cannot handle:**
- Datasets larger than RAM (no streaming/chunking)
- Real-time data ingestion
- Incremental model updates
- Distributed data processing

**Memory usage estimates:**
```
Dataset (404K pairs, 2 text columns):       ~200 MB (as strings)
TF-IDF matrix (323K × 5000):                ~3.2 GB (dense)
BERT embeddings (404K × 768, float32):      ~1.2 GB
All models loaded (ensemble):               ~2-5 GB
```

### 2.3 Model Parallelism — Score: 2/10

**Current state:** No parallelism.

- All models load and run on a single device
- Ensemble loads models sequentially (no parallel loading)
- No model sharding
- No GPU multi-processing

### 2.4 User Concurrency — Score: 2/10

**Current state:** No concurrency support.

- Streamlit locks per session — one request at a time
- No WebSocket or async support
- No request queue
- Session state is per-browser-tab (not thread-safe)

### 2.5 Horizontal Scaling — Score: 2/10

**Current state:** Not supported.

- No stateless design (models cached in process memory)
- No distributed cache (Redis/Memcached)
- No load balancer configuration
- No session affinity management

### 2.6 Vertical Scaling — Score: 5/10

**Current state:** Limited benefit from vertical scaling.

- More RAM helps: datasets, embeddings, models fit better
- Faster CPU helps: transformer inference improves
- GPU helps: bi-encoder and cross-encoder inference accelerates

**Diminishing returns:**
- Doubling CPU cores doesn't help single-request latency (single-threaded bottleneck)
- GPU benefits cross-encoder most (matrix ops) and bi-encoder partially
- Streamlit doesn't use multiple cores

---

## 3. Scalability Recommendations

### Short-term (High Impact, Low Effort)

1. **Pre-load models at startup** — Eliminate cold-start latency for first request
2. **Add batch prediction as default** — Batch encoding is 5-10x faster than per-pair encoding
3. **Reduce ensemble model count** — Test if 5-7 models give same accuracy as all 11
4. **Add response caching** — Cache predictions for identical Q1/Q2 pairs

### Medium-term (High Impact, Moderate Effort)

5. **Extract inference as API service** — Separate prediction server from Streamlit UI
6. **Add async inference** — Non-blocking prediction for batch processing
7. **Add request queuing** — Celery/Redis queue for batch prediction jobs
8. **Implement model warm-up** — Run dummy predictions at startup

### Long-term (High Impact, High Effort)

9. **Add model serving infrastructure** — TorchServe, Triton, or BentoML
10. **Add horizontal scaling** — Stateless design with distributed cache
11. **Add GPU sharing** — Multi-model GPU scheduling
12. **Add auto-scaling** — Kubernetes-based elastic scaling

---

## 4. Scalability Roadmap

```
Phase 0:  Document bottlenecks, add pre-loading, add response caching
Phase 1:  Extract inference API, add async support
Phase 2:  Add request queuing, model warm-up
Phase 3:  Add model serving infrastructure
Phase 4:  Add horizontal scaling, GPU sharing
```
