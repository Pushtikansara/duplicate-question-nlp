---
name: embeddings
description: Use when working with text embeddings and vector representations. Covers embedding models, generation techniques, dimensionality reduction, and similarity metrics.
---

# Embeddings Skill

## Instructions

### Embedding Fundamentals

1. **What Embeddings Represent** - Dense vectors in high-dimensional space where semantic similarity corresponds to spatial proximity. Similar concepts cluster together; analogies are represented as vector arithmetic. Each dimension captures latent semantic features.

2. **Embedding Dimensions** - Typical sizes: 384 (MiniLM), 768 (BERT-base), 1024 (BGE-large), 1536 (text-embedding-3-small), 3072 (text-embedding-3-large). Higher dimensions capture more nuanced semantics but increase storage and computation costs quadratically for search.

3. **Normalization** - L2 normalization projects vectors onto the unit sphere: `v = v / ||v||_2`. Normalized vectors make cosine similarity equal to dot product. Required for many ANN indexes. Normalize embeddings immediately after generation.

4. **Static vs Contextual** - Static embeddings (Word2Vec, GloVe, FastText) produce one vector per token regardless of context. Contextual embeddings (BERT, T5, LLaMA) produce different vectors based on surrounding tokens. Contextual always preferred for modern systems.

5. **Pooling Strategies** - Mean pooling (average all non-padded tokens), max pooling (element-wise maximum), CLS pooling (use [CLS] token), weighted pooling (attention-weighted, used in SBERT). Mean pooling with attention mask weighting is most robust.

### Embedding Models

1. **OpenAI Embeddings** - `text-embedding-3-small` (512 or 1536 dims, 62.3% MTEB), `text-embedding-3-large` (256 or 1024 or 3072 dims, 64.6% MTEB). API-based, you don't host. `dimensions` parameter enables Matryoshka truncation. Cost-effective for small-medium volumes.

2. **Sentence Transformers** - `all-MiniLM-L6-v2` (384 dims, fast, 58.8% MTEB), `all-mpnet-base-v2` (768 dims, 63.3% MTEB), `BAAI/bge-large-en-v1.5` (1024 dims, 64.2% MTEB), `intfloat/e5-mistral-7b-instruct` (4096 dims, 66.6% MTEB). Self-hosted, no API costs.

3. **Cohere Embeddings** - `embed-english-v3.0` (1024 dims, 64.5% MTEB), `embed-multilingual-v3.0` (1024 dims). API-based. Supports compression and search endpoints. Good multilingual support for 100+ languages.

4. **Multilingual Models** - `intfloat/multilingual-e5-large` (1024 dims), `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dims). Use when working with non-English text. Many embed all languages into the same space.

5. **Code Embeddings** - `microsoft/codebert-base` (768 dims), `sentence-transformers/code-search-msmarco` (768). Trained specifically for code retrieval. Embed function signatures, docstrings, and code snippets into searchable space.

6. **Instruction Embeddings** - E5, BGE, and Instructor models take prefixes: `query: {query}` or `passage: {document}`. The prefix instructs the model on the role of the input. For retrieval, use different prefixes for queries and documents.

### Embedding Generation

1. **Single Text** - `model.encode(text, normalize_embeddings=True)`. Returns a 1D numpy array. For Sentence Transformers, text is automatically truncated to `max_seq_length` (typically 128-512 tokens).

2. **Batch Processing** - `model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)`. Returns a 2D array of shape (N, dim). Use batch_size appropriate for GPU memory (64-256 for small models, 8-32 for large).

3. **Asymmetric Embedding** - Queries and documents may need different encoders or prefixes. For asymmetric tasks (retrieval), queries are often shorter and documents longer. Use `SeparateBackboneEncoder` or different instruction prefixes.

4. **Caching Embeddings** - Cache generated embeddings to avoid recomputation. Use disk cache (numpy `.npy` files) or database storage. Invalidate cache when the embedding model changes. Key by text hash and model name.

5. **Embedding Updates** - When documents change, regenerate embeddings for changed documents only. Maintain a last-modified timestamp per document. Periodic full re-indexing catches drift in the embedding model.

### Dimensionality Reduction

1. **PCA (Principal Component Analysis)** - Linear projection that preserves maximum variance. Reduce 1024 -> 256 while retaining 95%+ information. Fast to compute and apply. Use `sklearn.decomposition.PCA` with fit/transform.

2. **Matryoshka Representation Learning** - Train embeddings to be useful at multiple dimensions. Simply truncate the vector to desired dimension. Supported by OpenAI (`dimensions` parameter) and trained in Matryoshka models. No additional transform needed.

3. **t-SNE** - Non-linear reduction for visualization (typically 2D or 3D). Preserves local structure. Very slow on large datasets (use PCA first, then t-SNE). Use `perplexity=30`, `learning_rate=200`, `n_iter=1000`.

4. **UMAP** - Non-linear reduction faster than t-SNE. Preserves both local and global structure better than t-SNE. `n_neighbors=15`, `min_dist=0.1`. Good for visualization and as a preprocessing step for clustering.

5. **Intrinsic Dimensionality** - Measure how many dimensions actually encode signal vs noise. Compute with participation ratio or PCA eigenvalue analysis. Typical intrinsic dimension is 10-50x smaller than ambient dimension.

### Similarity Metrics

1. **Cosine Similarity** - `cos(a,b) = (a*b) / (||a|| * ||b||)`. Range [-1, 1]. Most common for text embeddings. For normalized vectors, reduces to dot product. Interpretation: 1.0 identical, 0.0 orthogonal, -1.0 opposite.

2. **Dot Product** - `a * b = sum(a_i * b_i)`. Range unbounded. Equivalent to cosine for normalized vectors. Used in many ANN indexes for efficiency. Sensitive to vector magnitude.

3. **Euclidean Distance** - `||a - b||_2 = sqrt(sum((a_i - b_i)^2))`. Range [0, inf). For normalized vectors, equivalent to cosine: `euclidean^2 = 2 - 2*cos`. Use when absolute distances matter.

4. **Inner Product** - Used for embeddings trained with inner product loss (e.g.,某些 recommender systems). Not equivalent to cosine. Requires specialized ANN indexes.

5. **Hellinger Distance** - `sqrt(sum((sqrt(a_i) - sqrt(b_i))^2))`. Range [0, sqrt(2)]. Appropriate for probability distribution embeddings. Less common but can outperform cosine for topic distributions.

### Quality Evaluation

1. **Intrinsic Evaluation** - Measure embedding quality directly: Spearman correlation on STS benchmarks, Recall@K on retrieval datasets, accuracy on downstream tasks. Use MTEB for standardized evaluation.

2. **Extrinsic Evaluation** - Measure end-task performance with embeddings: classification accuracy, retrieval precision, clustering purity. The ultimate measure of embedding quality for your use case.

3. **Ablation Experiments** - Compare embedding models by fixing everything else (chunking, retrieval, generation). Vary only the embedding model. Measure impact on end-task metrics, not just similarity scores.

4. **Out-of-Distribution Testing** - Evaluate embeddings on text types not seen during training. Performance on OOD data reveals the model's generalization. Important for production systems encountering diverse inputs.

5. **Dimensionality Sensitivity** - Test how performance changes with reduced dimensions. May find that 256 or 512 dimensions perform identically to full dimensions for your task, enabling significant storage savings.

## Examples

### Batch Encoding and Similarity Search

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')
corpus = ['Machine learning is transforming industries.',
          'Deep learning uses neural networks with many layers.',
          'Python is a popular programming language for AI.']
corpus_emb = model.encode(corpus, normalize_embeddings=True)

query = 'What is deep learning?'
query_emb = model.encode(query, normalize_embeddings=True)
scores = cosine_similarity([query_emb], corpus_emb)[0]
best_idx = np.argmax(scores)
print(f'Best match: {corpus[best_idx]} (score: {scores[best_idx]:.4f})')
```

### Dimensionality Reduction Pipeline

```python
from sklearn.decomposition import PCA
import numpy as np

embeddings = model.encode(all_texts, normalize_embeddings=False)
pca = PCA(n_components=128)
reduced = pca.fit_transform(embeddings)
reduced_normalized = reduced / np.linalg.norm(reduced, axis=1, keepdims=True)
print(f'Variance retained: {pca.explained_variance_ratio_.sum():.3f}')
```

### Matryoshka Embeddings (OpenAI)

```python
from openai import OpenAI

client = OpenAI()
response = client.embeddings.create(
    model='text-embedding-3-large',
    input='Your text here',
    dimensions=256,  # truncate to 256 dimensions
)
embedding_256d = response.data[0].embedding

# Same model, no truncation
response_full = client.embeddings.create(
    model='text-embedding-3-large',
    input='Your text here',
)
embedding_3072d = response_full.data[0].embedding
```

## Best Practices

1. **Always normalize** embeddings to unit length for consistent cosine similarity interpretation.
2. **Choose dimension based on task**: 384-768 for most retrieval, 1024+ for high-accuracy classification and clustering.
3. **Test 2-3 embedding models** on your specific data before committing; MTEB scores do not perfectly predict task performance.
4. **Use batch encoding** for efficiency; GPU memory typically supports 32-256 texts per batch.
5. **Cache embeddings** at every stage of the pipeline to avoid redundant computation.
6. **Set appropriate max_seq_length** for your data; longer documents need larger models with longer context windows.
7. **Consider multilingual models** even for English-dominant datasets if there is any non-English content.
8. **Update embeddings incrementally** rather than full re-index for frequently changing datasets.
9. **Monitor embedding drift** over time by comparing distributions of new vs existing embeddings.
10. **Backup embedding files** alongside document stores; regeneration is expensive and time-consuming.

## Common Mistakes

1. **Not normalizing embeddings** causing cosine similarity to not match expected values.
2. **Using context-insensitive models** (Word2Vec, GloVe) for tasks requiring contextual understanding.
3. **Ignoring input length limits** and silently truncating important content beyond max_seq_length.
4. **Model-query mismatch** - using a retrieval-pretrained model for clustering without understanding behavior.
5. **Applying PCA after normalization** disrupting the unit sphere geometry.
6. **Using default pooling** without understanding whether CLS, mean, or max is appropriate for the model.
7. **Evaluating only on STS** when the real task is retrieval or classification; metrics do not always correlate.
8. **Not versioning embeddings** alongside model versions, making debugging impossible.
9. **Over-reducing dimensions** losing signal necessary for the downstream task.
10. **Mixing embedding sources** (different models) in the same vector space without alignment.

## Libraries

- `sentence-transformers` - Primary library for text embeddings
- `openai` - OpenAI embedding API client
- `cohere` - Cohere embedding API client
- `transformers` - Raw model access for custom embedding extraction
- `scikit-learn` - PCA, t-SNE, cosine similarity, evaluation metrics
- `umap-learn` - UMAP for non-linear dimensionality reduction
- `numpy` - Efficient array operations and normalization
- `faiss` - Similarity search index construction
- `chromadb` - Vector storage with built-in embedding support
- `mteb` - Massive Text Embedding Benchmark for evaluation

## Design Principles

1. **Semantic Continuity** - Small changes in text produce small changes in embedding space.
2. **Dimensionality Sufficiency** - Use the minimum dimensions that achieve required performance.
3. **Model-Data Alignment** - Embedding model choice must match the distribution and task of the data.
4. **Normalization Independence** - Embeddings should be semantically meaningful before and after normalization.
5. **Loss Function Determines Space** - Contrastive loss creates separated clusters; MSE loss creates smooth space.
6. **Embeddings as Infrastructure** - Embeddings are a foundational layer; invest in quality and maintenance.
7. **Transferability** - Good embeddings transfer across tasks and domains without retraining.

## Coding Standards

1. **Model loading** - Load embedding model once on module init; reuse across all encoding calls.
2. **Normalization** - Apply `normalize_embeddings=True` in `model.encode()` calls consistently.
3. **Batch params** - Always set explicit `batch_size` and `show_progress_bar` in encoding calls.
4. **Dimension handling** - Assert embedding dimension consistency: `assert emb.shape[-1] == EXPECTED_DIM`.
5. **Cache keys** - Use `hashlib.md5(text.encode()).hexdigest() + '_' + model_name` as cache keys.
6. **Error handling** - Handle API errors for hosted embedding models with retry and fallback.
7. **Type hints** - Use `np.ndarray` return types; document shape as `(N, dim)`.
8. **Testing** - Test with similarity consistency: identical texts should have near-identical embeddings.
9. **Logging** - Log embedding model, dimension, batch size, and average encoding time per text.
10. **Reproducibility** - Set `torch.manual_seed()` and `np.random.seed()` before model initialization.
