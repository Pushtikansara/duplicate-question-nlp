---
name: vector-database
description: Use when working with vector databases for similarity search. Covers indexing, ANN algorithms, and integration with Pinecone, Weaviate, Qdrant, Chroma, Milvus.
---

# Vector Database Skill

## Instructions

### Core Concepts

1. **Vector Embeddings** - Dense numerical representations of data: text, images, audio, or any entity. Each vector is an array of floats (typically 384-7680 dimensions). Similar vectors represent semantically similar content.

2. **Similarity Metrics** - Cosine similarity (normalized vectors, range [-1,1]), Dot product (magnitude-aware), Euclidean/L2 distance (geometric distance), Manhattan distance (sum of absolute differences). Cosine is standard for text embeddings.

3. **Approximate Nearest Neighbor (ANN)** - Trade perfect accuracy for speed. Returns most similar vectors, not guaranteed exact nearest neighbors. Recall@10 typically 95-99%. Essential for datasets >10k vectors.

4. **Exact Nearest Neighbor** - Brute force comparison. O(n*d) complexity. Only feasible for datasets <10k vectors or when perfect accuracy is required. Use `faiss.IndexFlatIP` for exact search.

5. **Index Building** - Process of organizing vectors into a data structure for efficient search. Build time varies by algorithm: HNSW (minutes), IVF (fast), ScaNN (moderate). Index must be rebuilt when vectors are added or updated.

### ANN Algorithms

1. **HNSW (Hierarchical Navigable Small World)** - Multi-layer graph structure. Top layer has few nodes (coarse search), bottom has all nodes (fine search). Navigate from top to bottom. `M=16` (edges per node), `efConstruction=200` (build quality). Best recall/latency trade-off.

2. **IVF (Inverted File Index)** - Partition vectors into N centroids (k-means clustering). At search time, probe nearest centroids. `nlist=100` (number of centroids), `nprobe=10` (centroids to search). Faster build than HNSW, lower recall.

3. **IVF + PQ (Product Quantization)** - Compress vectors after IVF partitioning. Split vector into sub-vectors, quantize each to nearest centroid. Reduces memory 4-16x. `m=8` (sub-vectors), `nbits=8` (bits per sub-vector). Use when memory constrained.

4. **DiskANN** - SSD-based ANN index. Vectors stored on disk with compressed in-memory graph. Suitable for billion-scale datasets that don't fit in RAM. Lower throughput than in-memory indexes.

5. **ScaNN (Scalable Nearest Neighbors)** - Google's ANN algorithm. Uses anisotropic quantization and reordering. Optimized for dot product similarity. Often faster than HNSW on modern hardware. Available in `scann` package.

6. **LSH (Locality-Sensitive Hashing)** - Hash vectors into buckets with high collision probability for similar vectors. Each hash function is a random hyperplane. Use multiple hash tables for better recall. Simpler but lower recall than graph-based methods.

### Vector Database Platforms

1. **Chroma** - Lightweight, embedded. No external dependencies. Stores data in-memory or persisted to disk. Good for prototyping, development, small-to-medium datasets (<1M vectors). Python-native API. Limited production features.

2. **Pinecone** - Fully managed cloud service. Serverless and pod-based indexes. Handles scaling, backups, and monitoring. Pay-per-use pricing. High availability SLA. Best for production without DevOps overhead. Limited to 50k dimensions.

3. **Weaviate** - Open-source, self-hosted or cloud. Built-in vectorizer modules (OpenAI, Cohere, Hugging Face). GraphQL and REST APIs. Hybrid search (vector + keyword). Multi-tenancy support. CRUD operations on objects.

4. **Qdrant** - Open-source, written in Rust. High performance with low latency. Rich filtering with payload schema. Quantization support (scalar, product). Geo-search. Snapshots and replication. Point-in-time recovery.

5. **Milvus** - Cloud-native, distributed. GPU-accelerated indexing. Supports billion-scale datasets. ZooKeeper and etcd for coordination. Message storage with Pulsar or Kafka. Complex index management. Steepest learning curve.

6. **pgvector** - PostgreSQL extension. Adds vector type and similarity search to existing Postgres. Supports exact and approximate (IVFFlat, HNSW) search. Full SQL integration. ACID compliance. Best when already using PostgreSQL.

### Index Configuration

1. **Distance Metric** - Match metric to embedding model: sentence-transformers use cosine, OpenAI embeddings use cosine, Cohere uses dot product. Inconsistency between training and search metric degrades results.

2. **Index Parameters** - HNSW: `M` (8-64, higher = more memory but better recall), `ef_construction` (100-500, higher = slower build, better quality), `ef_search` (50-500, higher = better recall at query time).

3. **Memory Management** - Index size = num_vectors * dimensions * 4 bytes (float32). With HNSW overhead: ~2-10x more. With PQ: 0.25-1x more. Use 1/3 of available RAM as rough limit for in-memory indexes.

4. **Persistence** - Chroma saves to local SQLite + Parquet. Weaviate uses object storage. Qdrant uses RocksDB. Milvus uses MinIO/S3. pgvector uses PostgreSQL storage. Pinecone is fully managed.

### Advanced Operations

1. **Filtered Search** - Combine vector similarity with scalar filters. Pre-filter (filter first, then search) vs post-filter (search first, then filter). Pre-filter is faster when filter selectivity is high. Post-filter is better for broad filters.

2. **Batch Insert** - Insert vectors in batches of 100-1000 for optimal throughput. Smaller batches increase overhead, larger batches increase memory pressure. Use bulk insert for initial data loading.

3. **Index Optimization** - After large deletions, rebuild index to reclaim space and maintain search speed. Optimization window depends on delete frequency. Most databases have `optimize()` or `compact()` operations.

4. **Collection Management** - Create separate collections for different data types, use cases, or embedding models. Each collection has its own index configuration and schema. Rename, alias, or snapshot collections for blue-green deployments.

### Integration with LangChain

1. **Vector Store Interface** - LangChain provides `from_documents`, `from_texts`, `add_documents`, `similarity_search`, `as_retriever` for all vector databases. API differences are abstracted behind common interface.

2. **Retriever Options** - `search_type='similarity'` (default), `search_type='mmr'` (diverse results), `search_type='similarity_score_threshold'` (score filter). Configure `search_kwargs` for k, fetch_k, lambda_mult, score_threshold.

3. **Custom Parameters** - Pass database-specific params via `kwargs` in constructor: `collection_metadata` (Chroma), `distance_strategy` (Weaviate), `content_payload_key` (Qdrant), `consistency_level` (Milvus).

## Examples

### Chroma Basic Usage

```python
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.create_collection(
    name='documents',
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-MiniLM-L6-v2'),
    metadata={'hnsw:space': 'cosine'},
)

collection.add(
    ids=['doc1', 'doc2'],
    documents=['Machine learning is a subset of AI.', 'Python is a programming language.'],
    metadatas=[{'source': 'wiki', 'author': 'alice'}, {'source': 'docs', 'author': 'bob'}],
)

results = collection.query(query_texts=['What is AI?'], n_results=5, where={'source': 'wiki'})
```

### Qdrant with Filtering

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(path='./qdrant_db')
client.create_collection(
    collection_name='products',
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
    optimizers_config=models.OptimizersConfigDiff(default_segment_number=2),
)

client.upload_records(
    collection_name='products',
    records=[
        models.Record(id=i, vector=vector, payload={'category': 'electronics', 'price': 99.99})
        for i, vector in enumerate(vectors)
    ],
)

results = client.search(
    collection_name='products',
    query_vector=query_vec,
    limit=10,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(key='category', match=models.MatchValue(value='electronics')),
            models.FieldCondition(key='price', range=models.Range(gte=10.0, lte=500.0)),
        ]
    ),
)
```

### LangChain Integration

```python
from langchain_community.vectorstores import Chroma, Qdrant
from langchain_community.embeddings import OpenAIEmbeddings

chroma_store = Chroma.from_documents(docs, OpenAIEmbeddings(), persist_directory='./chroma_db')
chroma_retriever = chroma_store.as_retriever(search_kwargs={'k': 3, 'filter': {'source': 'wiki'}})

qdrant_store = Qdrant.from_documents(
    docs,
    OpenAIEmbeddings(),
    path='./qdrant_db',
    collection_name='my_docs',
    force_recreate=True,
)
results = qdrant_store.similarity_search_with_score('query', k=5)
```

## Best Practices

1. **Match distance metric** to the embedding model's training metric (typically cosine for text models).
2. **Benchmark ANN parameters** on your data distribution before production deployment.
3. **Use metadata filtering** to narrow search space before vector comparison for better accuracy.
4. **Monitor index build time** and schedule re-indexing during low-traffic periods.
5. **Set appropriate ef_search** (HNSW) or nprobe (IVF) at query time based on recall requirements.
6. **Shard indexes** across collections or databases when exceeding 10M vectors per index.
7. **Use quantization** (PQ, scalar) when memory is constrained but set aside capacity for re-ranking.
8. **Implement caching** for frequently queried vectors to reduce database load.
9. **Backup indexes** regularly; rebuilding large indexes is time-consuming and expensive.
10. **Version vector stores** alongside embedding model versions to ensure search consistency.

## Common Mistakes

1. **Mismatched distance metric** between embeddings and index causing semantically wrong results.
2. **Using exact search** on large datasets (>100k) leading to unacceptable query latency.
3. **Not tuning ANN parameters** using default values that may be suboptimal for data distribution.
4. **Ignoring memory requirements** for HNSW graphs (can be 10x vector size overhead).
5. **Over-filtering** with too many scalar conditions that reduce search quality by excluding relevant vectors.
6. **Re-indexing too frequently** during bulk inserts, causing high CPU usage and index fragmentation.
7. **Using default ef_search** that is too low for quality-sensitive applications.
8. **Inconsistent normalization** - vectors normalized during indexing but not at query time.
9. **DB connection pooling** not configured causing connection exhaustion under load.
10. **Not handling vector dimension mismatch** when embedding model is changed without re-indexing.

## Libraries

- `chromadb` - Embedded vector database, Python-native
- `qdrant-client` - Qdrant vector database client
- `weaviate-client` - Weaviate vector database client
- `pymilvus` - Milvus vector database SDK
- `pinecone-client` - Pinecone managed vector database client
- `pgvector` - PostgreSQL vector extension
- `faiss-cpu` / `faiss-gpu` - Low-level ANN index library
- `annoy` - Spotify's ANN library for static indexes
- `scann` - Google's scalable nearest neighbors
- `sentence-transformers` - Embedding model integration
- `langchain-community` - Unified vector store interface

## Design Principles

1. **Separation of Storage and Computation** - Store vectors persistently, build indexes in memory or GPU.
2. **Trade-off Triangle** - Accuracy, speed, and memory form a three-way trade-off; optimize for application constraints.
3. **Index as a Structure** - Index is a permanent data structure that must be managed, rebuilt, and versioned.
4. **Query-time Flexibility** - Search parameters (ef_search, nprobe) can be adjusted per query without re-indexing.
5. **Consistency Models** - Most vector databases offer eventual consistency; design for stale reads tolerance.
6. **Filter Pushdown** - Filters should execute before or during vector search, never as post-processing for production.
7. **Dimensionality as Cost** - Search complexity scales linearly with dimensions; use the minimum viable dimensionality.

## Coding Standards

1. **Connection management** - Use context managers or singleton patterns for client connections.
2. **Collection naming** - Use semantic names: `{project}_{env}_{data_type}` (e.g., `rag_prod_docs`).
3. **Error handling** - Handle `ServiceUnavailable`, `NotFound`, `DuplicateError` from database operations.
4. **Batch operations** - Always batch inserts; never insert one vector at a time in loops.
5. **Configuration** - Store index parameters in config files, not hardcoded in application code.
6. **Logging** - Log query latency, index build time, search recall, and error rates.
7. **Testing** - Test with small random vectors in CI; benchmark with realistic data volumes.
8. **Retry logic** - Implement exponential backoff for transient failures during insert and search.
9. **Schema documentation** - Document vector dimension, distance metric, metadata schema, and index type.
10. **Monitoring** - Track index size, query latency p50/p99, recall@k, and write throughput.
