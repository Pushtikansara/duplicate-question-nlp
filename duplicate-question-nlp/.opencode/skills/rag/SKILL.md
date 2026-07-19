---
name: rag
description: Use when implementing Retrieval-Augmented Generation systems. Covers document chunking, embedding, retrieval, generation, and evaluation.
---

# RAG Skill

## Instructions

### Document Loading

1. **Loaders by Source** - `PyPDFLoader` (PDFs), `TextLoader` (text files), `CSVLoader` (tabular data), `UnstructuredMarkdownLoader` (markdown), `NotionDirectoryLoader` (Notion export), `S3FileLoader` (AWS S3). Use `langchain_community.document_loaders` for 100+ formats.

2. **Web Loading** - `WebBaseLoader` for simple HTML, `SeleniumURLLoader` for JavaScript-rendered pages, `AsyncHtmlLoader` for batch crawling. Use `RecursiveUrlLoader` for site-wide scraping with depth control.

3. **Database Loading** - `SQLDatabaseLoader` for relational databases. Construct queries to fetch relevant text columns. Use `DatabaseLoader` with `metadata_columns` to preserve row metadata alongside content.

4. **API Loading** - `GitHubLoader` for repos, `ConfluenceLoader` for wiki pages, `SlackLoader` for messages, `YouTubeLoader` for transcripts. Each loader handles authentication and pagination internally.

### Document Chunking

1. **RecursiveCharacterTextSplitter** - Preferred for most use cases. Splits on `["\n\n", "\n", " ", ""]` recursively. Default `chunk_size=1000`, `chunk_overlap=200`. The overlap maintains context across chunk boundaries.

2. **Semantic Chunker** - Splits based on semantic similarity between consecutive sentences. Uses embeddings to detect topic boundaries. `from langchain_experimental.text_splitter import SemanticChunker`. Requires an embedding model.

3. **TokenTextSplitter** - Splits at token boundaries rather than characters. Use when the downstream model has strict token limits. `chunk_size` is in tokens. Compatible with Hugging Face tokenizers.

4. **MarkdownHeaderTextSplitter** - Preserves document structure by splitting on markdown headers. Returns chunks with metadata containing header hierarchy. Essential for documents where section context matters.

5. **Code Splitter** - Language-aware splitting for code files. Supports Python, JS, TypeScript, Java, and more. Uses abstract syntax tree (AST) to split at function/class boundaries. Preserves code structure.

6. **Chunking Strategy** - General rule: smaller chunks (256-512 tokens) for focused retrieval, larger chunks (512-1024) for comprehensive context. Overlap of 10-20% of chunk size. Optimize chunk size empirically with retrieval evaluation.

### Embedding

1. **Embedding Models** - Use `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fast), `text-embedding-3-small` (512-dim, good accuracy), `text-embedding-3-large` (2560-dim, best quality), `BAAI/bge-large-en-v1.5` (1024-dim, open-source).

2. **Embedding Dimensions** - Higher dimensions capture more information but increase storage and search cost. 768-1024 dimensions is standard. Use dimensionality reduction (Matryoshka embeddings) for flexible trade-offs.

3. **Multi-vector Embedding** - Generate multiple embeddings per document: summary embedding, chunk embeddings, and hypothetical questions. Improves retrieval recall by capturing different representations of the same content.

4. **ColBERT** - Token-level late interaction: each query token interacts with each document token at scoring time. Higher accuracy than bi-encoders but slower. Use for re-ranking in two-stage retrieval.

### Retrieval

1. **Similarity Search** - `vectorstore.similarity_search(query, k=4)` returns k nearest chunks by cosine/dot product. `similarity_search_with_score` returns distance scores. `similarity_search_with_relevance_scores` returns normalized scores.

2. **Maximum Marginal Relevance** - `vectorstore.max_marginal_fetch_search(query, k=4, fetch_k=20)`. Diversifies results by penalizing redundancy with already-selected documents. Balances relevance and diversity.

3. **Hybrid Search** - Combine dense (embedding) and sparse (BM25) retrieval. Use `EnsembleRetriever` for weighted fusion. BM25 captures lexical matching, embeddings capture semantic matching. Typically 0.5 weight each.

4. **Multi-Query Retrieval** - Generate N query variations using LLM, retrieve for each, deduplicate results. Handles cases where single query misses relevant context due to phrasing. Cost: Nx more retrieval calls.

5. **HyDE (Hypothetical Document Embeddings)** - Generate a hypothetical document that answers the query, embed that instead of the query. The hypothetical document is closer in embedding space to relevant documents than the query is.

6. **Fusion Retrieval** - Reciprocal Rank Fusion combines multiple result lists: `score = sum(1 / (k + rank_i))`. Used to merge results from different retrievers, modalities, or query variations.

### Generation

1. **Context Integration** - Insert retrieved chunks into prompt template: `Context: {context}\n\nQuestion: {question}\n\nAnswer:`. Order chunks by relevance. Limit context to model's context window minus prompt and generation.

2. **Prompt Templates** - Use specific instructions based on task: `Answer using only the provided context. If uncertain, say "I don't know".` Include source attribution requirement. Avoid extraction-style prompts for generative tasks.

3. **Citation Generation** - Include source identifiers in context: `[Source: doc_id, page X]`. Instruct model to cite sources inline. Post-process to format citations consistently. Verify citation accuracy against retrieved chunks.

4. **Streaming Generation** - Generate answers token by token for responsive UX. Stream retrieved chunks alongside answer for transparent grounding. Use `stream()` or `astream()` on the RAG chain.

### RAG Architectures

1. **Naive RAG** - Retrieve top-k chunks, concatenate, generate. Simple but limited: single retrieval, no query refinement, fixed chunk selection. Suitable for simple QA on moderate-sized corpora.

2. **Advanced RAG** - Pre-retrieval: query rewriting, query expansion, HyDE. Post-retrieval: re-ranking, filtering, compression, fusion. Iterative retrieval for complex multi-hop questions.

3. **Self-RAG** - Retrieve chunks, generate answers with reflection tokens, evaluate relevance and completeness, adaptively retrieve more if needed. Self-RAG models are fine-tuned to produce special reflection tokens.

4. **Corrective RAG** - After initial retrieval, evaluate chunk relevance. If insufficient, rewrite query and re-retrieve rather than generating from poor context. Grade chunks for relevance before generation.

5. **Adaptive RAG** - Route queries to appropriate strategy: simple queries use direct generation, factoid queries use single retrieval, complex queries use iterative retrieval. Use classifier or LLM routing.

### Evaluation

1. **Retrieval Metrics** - `hit_rate` (was relevant doc in top-k), `MRR` (mean reciprocal rank of first relevant), `NDCG@k` (graded relevance), `precision@k`, `recall@k`. Use `ragas` or `langchain.evaluation`.

2. **Generation Metrics** - `faithfulness` (is answer supported by context), `answer_relevancy` (does answer address question), `context_precision` (how much context was relevant), `context_recall` (was all needed context retrieved).

3. **End-to-End Metrics** - Human evaluation on a test set of query-answer pairs. Automated with LLM-as-judge: use GPT-4 to score answer quality on 1-5 scale. Track over time as system evolves.

4. **Ablation Studies** - Test each component independently: chunk size, chunk overlap, embedding model, retriever type, top-k, re-ranker. One-variable-at-a-time changes. Use standardized test set.

## Examples

### Basic RAG Chain

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(documents)
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={'k': 4})

prompt = ChatPromptTemplate.from_template('''Answer based on context:
Context: {context}
Question: {question}
Answer:''')

def format_docs(docs):
    return '\n\n'.join(doc.page_content for doc in docs)

chain = (
    {'context': retriever | format_docs, 'question': RunnablePassthrough()}
    | prompt
    | ChatOpenAI(model='gpt-4o-mini')
    | StrOutputParser()
)

result = chain.invoke('What is the capital of France?')
```

### Advanced RAG with Re-ranking

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from sentence_transformers import CrossEncoder

reranker = CrossEncoderReranker(
    model=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'),
    top_n=3,
)
compressor = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=retriever,
)
results = compressor.invoke('What is machine learning?')
```

### RAG with Query Transformation

```python
def rewrite_query(question: str) -> str:
    messages = [
        SystemMessage('Rewrite the question for web search. Make it more specific and search-friendly.'),
        HumanMessage(question),
    ]
    return model.invoke(messages).content

def multi_query_retrieval(question: str) -> list:
    queries = [rewrite_query(f'{question} aspect {i}') for i in range(3)]
    all_docs = []
    for q in queries:
        all_docs.extend(vectorstore.similarity_search(q, k=3))
    return unique_by_content(all_docs)

chain = RunnableLambda(multi_query_retrieval) | format_docs | prompt | model
```

## Best Practices

1. **Chunk at semantic boundaries** using markdown headers or sentence boundaries, not arbitrary character counts.
2. **Include metadata** in chunks (source URL, page number, section title) for citation and filtering.
3. **Use hybrid search** (dense + sparse) for production systems to capture both semantic and lexical matches.
4. **Implement re-ranking** with cross-encoders for the top 20-50 retrieved chunks before generation.
5. **Set appropriate top-k** based on context window: typically 3-10 chunks depending on chunk size.
6. **Filter by metadata** (date, source, domain) to constrain retrieval to relevant subsets.
7. **Log all retrieval queries and results** for debugging and improving chunking/embedding strategies.
8. **Test with edge cases**: empty results, irrelevant context, conflicting information across chunks.
9. **Monitor chunk utilization** to identify chunks that are never retrieved or always retrieved.
10. **Version your embedding models** and re-index when updating to maintain consistency.

## Common Mistakes

1. **Lossy chunking** that splits sentences or code blocks mid-structure, breaking meaning.
2. **Missing context** from insufficient chunk overlap, causing truncation of important information.
3. **Ignoring metadata** when chunks from different sources are mixed without provenance tracking.
4. **Context overflow** from retrieving too many chunks for the model's context window.
5. **No re-ranking** causing top chunks to be less relevant than lower-ranked alternatives.
6. **Stale embeddings** when documents are updated but vector store is not re-indexed.
7. **Single query retrieval** for multi-faceted questions that need multiple retrieval passes.
8. **Hallucination from conflicting context** where different chunks provide contradictory information.
9. **Chunking without respect to document structure** losing hierarchical relationships between sections.
10. **Not handling empty retrieval results** leading to generation without any context.

## Libraries

- `langchain` - RAG chain orchestration and document loaders
- `langchain-community` - Additional document loaders and retrievers
- `chromadb` - Lightweight vector store for development and prototyping
- `faiss-cpu` / `faiss-gpu` - Fast nearest neighbor search index
- `pypdf` / `pypdfium2` - PDF document loading
- `unstructured` - Unstructured document parsing (PDFs, HTML, DOCX, images)
- `ragas` - RAG evaluation metrics
- `sentence-transformers` - Embedding models and cross-encoders for re-ranking
- `tiktoken` - Token counting for context window management
- `nltk` / `spacy` - Sentence boundary detection for semantic chunking

## Design Principles

1. **Grounding** - Every generated statement must be traceable to a retrieved source document.
2. **Retrieval Quality over Generation Quality** - Better retrieval always improves generation; the reverse is not true.
3. **Progressive Enhancement** - Start with naive RAG, add improvements as needed based on evaluation.
4. **Stateless Retrieval** - Each retrieval call is independent of previous calls; state is in the vector index.
5. **Modular Components** - Each stage (loading, chunking, embedding, retrieval, generation) is independently replaceable.
6. **Attribution** - Retrieved sources must be visible to the user for trust and verification.
7. **Cost Proportionality** - Retrieval cost scales with corpus size; generation cost scales with output length.

## Coding Standards

1. **Data flow** - Use LCEL for composing RAG chains: `retriever | formatter | prompt | model | parser`.
2. **Chunk configuration** - Store chunking params in config dict: `chunk_size`, `chunk_overlap`, `separators`.
3. **Embedding management** - Load embedding model once, reuse across queries; cache embeddings to disk.
4. **Error handling** - Wrap retrieval in try/except; return graceful message on retrieval failure.
5. **Metadata propagation** - Preserve document metadata through chunking, retrieval, and generation steps.
6. **Logging** - Log query, retrieved chunks (with scores), generated answer, and latency per request.
7. **Testing** - Test chunking on real documents, validate retrieval with known queries, evaluate generation with test set.
8. **Configuration** - Expose chunk size, top-k, model selection, and retrieval type as config parameters.
9. **Versioning** - Tag vector stores with embedding model version and date for reproducibility.
10. **Monitoring** - Track retrieval hit rate, generation faithfulness, end-to-end latency, and user feedback scores.
