---
name: sentence-transformers
description: Use when generating sentence embeddings and semantic similarity using Sentence-Transformers. Covers SBERT, cross-encoders, training, and applications.
---

# Sentence-Transformers Skill

## Instructions

### SBERT Architecture

1. **Bi-Encoder** - Two identical BERT/RoBERTa networks with weight sharing. Each sentence is encoded independently into a fixed-size vector. Inference is O(n+m) where n and m are sentence lengths. Suitable for large-scale similarity search and clustering.

2. **Pooling Strategy** - After the transformer backbone, apply a pooling layer: `MEAN` (average all token embeddings), `MAX` (max over tokens), `CLS` (use [CLS] token). MEAN pooling is recommended for most use cases. Set `pooling_mode_mean_tokens=True`.

3. **Normalization** - Apply L2 normalization to output embeddings so cosine similarity equals dot product. Use `nn.functional.normalize(emb, p=2, dim=1)`. Normalized embeddings have unit length and enable `cos_sim = embeddings @ embeddings.T`.

4. **Similarity Computation** - Cosine similarity is standard: `cos_sim(a, b) = a * b / (||a|| * ||b||)`. For normalized vectors, this simplifies to dot product. Also supported: euclidean distance, manhattan distance, and dot product.

### Cross-Encoder

1. **Architecture** - Single BERT taking both sentences as input with `[SEP]` token. Outputs a single similarity score. Has O(n+m) computation per pair. Not suitable for retrieval but excellent for re-ranking.

2. **Use Case** - Cross-encoders are 10-100x slower than bi-encoders per pair but 1-2% more accurate for NLI and STS tasks. Use as final re-ranker after bi-encoder candidate retrieval. Process top-K candidates (typically 100).

3. **Output Types** - Regression (single score, sigmoid for [0,1]), classification (softmax over classes), or ranking (comparison of two pairs). Specify `num_labels=1` for regression and `num_labels=num_classes` for classification.

### Training

1. **Softmax Loss** - Good for NLI tasks with multiple classes. Triples `(anchor, positive, negative)` processed through bi-encoder. Softmax over similarity scores for each class. Use `SoftmaxLoss(model, sentence_embedding_dim, num_labels)`.

2. **Contrastive Loss** - Works with pairs and label (1 for similar, 0 for dissimilar). Margin-based loss: pull similar pairs together, push dissimilar pairs apart by at least margin. Use `ContrastiveLoss(model, margin=0.5)`.

3. **Triplet Loss** - Uses `(anchor, positive, negative)` triples. Maximize anchor-positive similarity, minimize anchor-negative similarity. Use `TripletLoss(model, distance_metric=SiameseDistanceMetric.COSINE_DISTANCE, triplet_margin=5)`.

4. **Multiple Negatives Ranking Loss** - Best for retrieval tasks. In a batch of `(anchor, positive)` pairs, treat all other positives as negatives for each anchor. Very efficient as it leverages batch structure. Use `MultipleNegativesRankingLoss(model)`.

5. **CoSENT Loss** - Scale-based loss using ordered pairs. Given pairs with similarity scores, minimize MSE between predicted and target cosine similarity. Good for STS fine-tuning. Use `CoSENTLoss(model)`.

6. **Adaptive Loss** - Use `AdaptiveLayerLoss` for training with layer-wise learning rates. Lower layers get smaller updates, preserving pretrained knowledge while adapting top layers.

7. **Distillation** - Train a smaller student model from a larger teacher model using `DistillationLoss`. Student mimics teacher's similarity scores. Achieves 90%+ of teacher performance at 5-10x fewer parameters.

### Training Data Format

1. **Labeled Pairs** - `InputExample(texts=['sentence1', 'sentence2'], label=score_or_class)`. Score for regression, class index for classification. Used with ContrastiveLoss or SoftmaxLoss.

2. **Triples** - `InputExample(texts=['anchor', 'positive', 'negative'])`. No label needed. Used with TripletLoss or MultipleNegativesRankingLoss.

3. **Datasets** - Load with `datasets.load_dataset` and convert to `InputExample` list. For large datasets, create a custom `DataLoader` that yields batches of text pairs.

### Inference Pipeline

1. **Encoding** - `model.encode(sentences, batch_size=64, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)`. For large sets, process in batches to manage GPU memory.

2. **Similarity Search** - Encode query and corpus separately. Use `util.cos_sim(query_emb, corpus_emb)` for dense similarity. For large corpora (>10k), use `util.semantic_search(query_emb, corpus_emb, top_k=100)`.

3. **Caching** - Pre-compute and cache corpus embeddings. Update incrementally when new documents are added. Store in numpy format or pickle. Embeddings are static unless the model is fine-tuned.

### Applications

1. **Semantic Textual Similarity (STS)** - Direct pair scoring. Evaluate with Spearman correlation to human judgments. Key benchmark: STS-Benchmark. Best models achieve >85 Spearman.

2. **Semantic Search** - Encode corpus documents offline. Encode query at runtime. Find nearest neighbors by cosine similarity. Add a cross-encoder re-ranker for top-100 candidates.

3. **Clustering** - Use `kmeans` or `HDBSCAN` on embeddings for document clustering. Pre-normalize embeddings. Tune cluster count with silhouette score or elbow method.

4. **Duplicate Detection** - Set similarity threshold (typically 0.8-0.95). Flag pairs exceeding threshold as potential duplicates. Used for question deduplication, document merging.

5. **Text Classification** - Alternative to fine-tuning BERT directly: encode text with SBERT, train a lightweight classifier (Logistic Regression, SVM, XGBoost) on embeddings. Faster iteration and supports domain adaptation.

6. **Retrieval-Augmented Generation** - Encode knowledge base documents. Retrieve top-k relevant chunks. Pass to LLM as context. Critical for grounding LLM responses in factual data.

## Examples

### Basic Encoding and Similarity

```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = ['A man is eating food.', 'A man is eating pasta.', 'A woman is cooking.']
embeddings = model.encode(sentences, normalize_embeddings=True)

similarity_matrix = util.cos_sim(embeddings, embeddings)
print(similarity_matrix)
# tensor([[1.0000, 0.9500, 0.6842],
#         [0.9500, 1.0000, 0.6723],
#         [0.6842, 0.6723, 1.0000]])
```

### Training with MultipleNegativesRankingLoss

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

model = SentenceTransformer('distilbert-base-nli-mean-tokens')
train_examples = [
    InputExample(texts=['What is AI?', 'Artificial Intelligence is the simulation of human intelligence']),
    InputExample(texts=['Python programming', 'Python is a high-level programming language']),
]
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.MultipleNegativesRankingLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path='./fine-tuned-model',
    show_progress_bar=True,
)
```

### Semantic Search Pipeline

```python
corpus = ['Document 1 text...', 'Document 2 text...', 'Document 3 text...']
corpus_embeddings = model.encode(corpus, convert_to_tensor=True, normalize_embeddings=True)

query = 'What is the capital of France?'
query_embedding = model.encode(query, convert_to_tensor=True, normalize_embeddings=True)

hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)[0]
for hit in hits:
    print(f'{hit["score"]:.4f}: {corpus[hit["corpus_id"]]}')
```

## Best Practices

1. **Normalize embeddings** at both training and inference time for consistent cosine similarity.
2. **Use `MultipleNegativesRankingLoss`** for retrieval tasks; it is the most sample-efficient loss.
3. **Pre-tokenize and cache** encoded corpus for production retrieval systems.
4. **Use cross-encoder re-ranking** for applications requiring high accuracy on top results.
5. **Choose model size based on throughput needs**: MiniLM for high throughput, MPNet for accuracy.
6. **Evaluate with Spearman correlation** for STS and Recall@K for retrieval tasks.
7. **Warm up learning rate** for 10% of training steps to stabilize fine-tuning.
8. **Use `model.max_seq_length`** to control truncation; longer sequences increase compute quadratically.
9. **Fine-tune on domain-specific data** to improve accuracy for specialized domains.
10. **Monitor embedding distribution** with PCA/t-SNE to detect mode collapse or cluster drift.

## Common Mistakes

1. **Not normalizing embeddings** leading to inconsistent similarity scores across models.
2. **Using cross-encoder for large-scale retrieval** instead of bi-encoder; extremely slow for >10k candidates.
3. **Training with wrong loss function** - using contrastive loss for retrieval when multiple negatives is better.
4. **Inconsistent pooling strategy** between training and inference causing degraded performance.
5. **Ignoring `normalize_embeddings` parameter** and getting unnormalized vectors from encode.
6. **Using BERT directly** (without SentenceTransformer wrapper) and averaging suboptimal layer representations.
7. **Not handling out-of-vocabulary tokens** for domain-specific terminology during fine-tuning.
8. **Overlapping train/eval pairs** causing inflated similarity scores during evaluation.
9. **Training with too small batch size** (< 8) for MultipleNegativesRankingLoss; negatives within batch are sparse.
10. **Not cleaning text** before encoding; artifacts, HTML tags, and special characters affect embeddings.

## Libraries

- `sentence-transformers` - Core library for dense text embeddings
- `datasets` - Loading and preprocessing training data
- `transformers` - Backbone model architectures
- `faiss` - Fast similarity search index for large-scale retrieval
- `annoy` - Approximate nearest neighbor search
- `scikit-learn` - Evaluation metrics (Spearman, Pearson) and clustering
- `umap-learn` - Dimensionality reduction for embedding visualization
- `hdbscan` - Density-based clustering for embeddings
- `evaluate` - Standardized evaluation metrics from Hugging Face
- `nlpaug` - Text augmentation for training data expansion

## Design Principles

1. **Semantic Equivalence** - Sentences with similar meaning should have similar embeddings regardless of surface form.
2. **Efficient Retrieval** - Bi-encoder architecture enables sub-linear similarity search via approximate nearest neighbors.
3. **Transfer Learning** - Pretrained language models provide strong semantic priors; fine-tuning adapts to specific tasks.
4. **Asymmetric Encoding** - Queries and documents can use different encoders but must embed to the same space.
5. **Scale-Invariant** - Embeddings should be normalized to enable consistent distance thresholds across domains.
6. **Composable** - SBERT embeddings can feed into any downstream system (search, clustering, classification, RAG).
7. **Loss-Driven Training** - Choice of loss function is the primary lever for task-specific behavior.

## Coding Standards

1. **Model loading** - Use `SentenceTransformer('model-name')` with explicit revision pinning.
2. **Encoding parameters** - Always specify `normalize_embeddings=True` and `convert_to_numpy=True` for consistency.
3. **Training configuration** - Define all hyperparameters (batch_size, epochs, warmup_steps, eval_steps) upfront.
4. **Loss instantiation** - Match loss function to task: retrieval uses MultipleNegativesRankingLoss, STS uses CoSENTLoss.
5. **Evaluation protocol** - Compute Spearman correlation for STS; Mean Reciprocal Rank and Recall@K for retrieval.
6. **Logging** - Log loss, learning rate, and evaluation metrics at regular intervals during training.
7. **Checkpointing** - Save model every N steps; save best model separately based on evaluation metric.
8. **Inference batching** - Process queries in batches of 32-128 for optimal GPU utilization.
9. **Cache management** - Store corpus embeddings as numpy arrays with versioned file names.
10. **Reproducibility** - Set `torch.manual_seed`, `np.random.seed`, and `transformers.set_seed` before training.
