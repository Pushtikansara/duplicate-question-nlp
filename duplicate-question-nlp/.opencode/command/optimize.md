---
description: Optimize code for performance and efficiency.
---

# Performance Optimization Prompt

You are tasked with optimizing the following code for performance and resource efficiency.

## Input

{{input}}

## Optimization Methodology

Follow a systematic approach: measure, identify bottlenecks, optimize, verify.

### Step 1: Establish Baseline

- Measure current execution time, memory usage, CPU utilization, I/O operations, and network requests.
- Identify the critical path and hot spots through profiling.
- Set performance targets (e.g., response time under 200ms, memory under 256MB).

### Step 2: Algorithmic Complexity

- Analyze time complexity (Big O) of all algorithms and data structures.
- Look for O(n^2) or worse operations that can be improved.
- Consider alternative data structures: hash maps for lookup, trees for ordered data, tries for string operations, bloom filters for set membership.
- Evaluate sorting, searching, and traversal algorithms.
- Replace brute-force approaches with more efficient algorithms.

### Step 3: Memory Optimization

- Profile memory allocation and garbage collection patterns.
- Identify memory leaks, excessive allocations, and object retention.
- Use object pooling for frequently created/destroyed objects.
- Lazy-load expensive resources only when needed.
- Use weak references where appropriate to avoid preventing garbage collection.
- Optimize data structure sizes and consider memory alignment.

### Step 4: Caching Strategies

- Identify computations or data fetches that produce the same result repeatedly.
- Implement appropriate caching layers:
  - In-memory cache (LRU, LFU, TTL-based eviction)
  - Distributed cache (Redis, Memcached)
  - HTTP caching (ETags, Cache-Control headers, CDN)
  - Database query cache (materialized views, query result cache)
- Consider cache invalidation strategies: time-based, event-based, write-through, write-behind.

### Step 5: Concurrency and Async

- Identify serial bottlenecks that could run in parallel.
- Use async/await for I/O-bound operations (file reads, network calls, database queries).
- Use multiprocessing/threading for CPU-bound operations (being mindful of GIL in Python).
- Implement connection pooling for database and HTTP connections.
- Consider message queues for decoupling and load leveling.
- Use actors, channels, or other concurrency models where appropriate.

### Step 6: Database Optimization

- Analyze query execution plans and add missing indexes.
- Reduce N+1 query problems through eager loading, batching, or joins.
- Use database connection pooling.
- Consider read replicas for read-heavy workloads.
- Implement pagination for large result sets (cursor-based over offset-based).
- Denormalize where read performance is critical.

### Step 7: I/O and Network

- Batch file operations and network requests.
- Use buffered I/O streams.
- Compress data in transit and at rest.
- Use connection reuse (keep-alive) for network connections.
- Consider protocol buffers, message pack, or other efficient serialization.

### Step 8: Frontend / Rendering

- Analyze Core Web Vitals: LCP, FID, CLS, INP.
- Code-split bundles and lazy-load non-critical components.
- Virtualize long lists (react-window, react-virtualized).
- Debounce and throttle expensive event handlers.
- Optimize images (lazy loading, responsive images, WebP/AVIF, compression).
- Minimize DOM size and reflows/repaints.
- Tree-shake unused code and remove dead CSS.

## Output Format

### Optimization Report

#### Baseline Metrics
- Execution time: X ms
- Memory usage: Y MB
- Database queries: Z
- API calls: W

#### Issues Found

```
### [P0/P1/P2/P3] Issue Title

- **Location**: file:line
- **Severity**: P0 (blocking) / P1 (critical) / P2 (major) / P3 (minor)
- **Current Behavior**: what is happening
- **Root Cause**: why it is slow
- **Optimization**: specific change to make
- **Expected Improvement**: estimated performance gain
- **Code Change**:

\`\`\`language
// before vs after
\`\`\`
```

#### Final Results
- Execution time: X ms (improvement: X%)
- Memory usage: Y MB (improvement: Y%)
- Database queries: Z (reduction: Z%)
- API calls: W (reduction: W%)
