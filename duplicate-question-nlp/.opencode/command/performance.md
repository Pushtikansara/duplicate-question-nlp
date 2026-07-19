---
description: Analyze and improve application performance.
---

# Performance Analysis and Optimization Prompt

You are tasked with analyzing the performance characteristics of the following application and providing targeted improvements.

## Input

{{input}}

## Performance Analysis Methodology

### Phase 1: Establish Baselines

Before making changes, measure the current state:

**Performance Metrics to Collect**:

| Category | Metric | Tool |
|----------|--------|------|
| Response time | p50, p95, p99 latency | APM (Datadog, New Relic), wrk, k6 |
| Throughput | Requests per second (RPS) | Load testing tools |
| Error rate | HTTP 5xx, exceptions | APM, logging |
| CPU | User, system, idle, iowait | top, htop, perf, strace |
| Memory | RSS, heap, GC pauses | valgrind, heap profiler, jemalloc stats |
| Disk | IOPS, throughput, latency | iostat, iotop, fio |
| Network | Bandwidth, packet loss, latency | iftop, netstat, tcpdump |
| Database | Query latency, slow queries, connections | pg_stat_statements, slow query log, EXPLAIN ANALYZE |
| Frontend | LCP, FID, CLS, INP, TTFB | Lighthouse, Web Vitals, Chrome DevTools |

### Phase 2: Identify Bottlenecks

**Common Bottleneck Patterns**:

**CPU-bound**:
- Tight loops with heavy computation
- Inefficient algorithms (O(n^2) where O(n log n) is possible)
- Excessive serialization/deserialization
- Synchronous processing that could be parallelized
- Regular expression backtracking catastrophes

**Memory-bound**:
- Memory leaks (objects not released, closures holding references)
- Excessive object allocation and GC pressure
- Large object graphs kept in memory
- Unbounded caches that grow without eviction
- Buffer bloat (overly large buffers pre-allocated)

**I/O-bound**:
- N+1 database queries
- Missing database indexes
- Synchronous file reads on critical path
- Chatty API calls (many small requests instead of batched)
- Connection pool exhaustion
- Lock contention on shared resources

**Network-bound**:
- Large payloads (uncompressed, unnecessary data)
- Chatty protocols (many round trips)
- DNS resolution latency
- TLS handshake overhead
- Suboptimal CDN configuration

### Phase 3: Backend Optimization

**Application-Level**:

- **Caching**:
  - Application cache (LRU, TTL-based) for expensive computations
  - HTTP caching headers (Cache-Control, ETag, Last-Modified)
  - CDN caching for static and semi-static content
  - Database query cache (materialized views, Redis)
  - Session caching (Redis, Memcached)

- **Concurrency**:
  - Use async/await for I/O-bound operations
  - Use worker threads/processes for CPU-bound operations
  - Implement connection pooling (DB, HTTP, Redis)
  - Use message queues for background jobs
  - Consider event-driven architecture with event streaming

- **Algorithm Optimization**:
  - Profile hot paths and optimize the inner loops
  - Replace recursive algorithms with iterative where applicable
  - Use appropriate data structures (HashMap for lookup, sorted sets for ranges)
  - Implement early termination and short-circuit evaluation
  - Use lazy evaluation for expensive operations

- **Database Optimization**:
  - Add missing indexes (check EXPLAIN plans)
  - Rewrite slow queries (avoid SELECT *, use covering indexes)
  - Implement query batching and bulk operations
  - Use read replicas for read-heavy workloads
  - Partition large tables
  - Implement cursor-based pagination
  - Connection pooling and query timeouts

**Infrastructure-Level**:

- Horizontal scaling (add more instances)
- Vertical scaling (upgrade instance size)
- Auto-scaling based on metrics
- Load balancer configuration
- Database read replicas and sharding
- CDN and edge computing
- Content compression (gzip, brotli)

### Phase 4: Frontend Optimization

**Core Web Vitals**:

- **LCP (Largest Contentful Paint) < 2.5s**:
  - Optimize images (next-gen formats, compression, responsive)
  - Preload critical resources
  - Server-side render or statically generate above-the-fold content
  - Minimize render-blocking resources
  - Use CDN with edge caching

- **FID (First Input Delay) < 100ms** / **INP (Interaction to Next Paint) < 200ms**:
  - Code-split JavaScript bundles
  - Defer non-critical scripts
  - Minimize main thread work
  - Use web workers for heavy computation
  - Implement virtual scrolling for long lists

- **CLS (Cumulative Layout Shift) < 0.1**:
  - Set explicit dimensions on images and embeds
  - Reserve space for dynamic content (ads, embeds)
  - Avoid inserting content above existing content
  - Use font-display: optional or swap

**Asset Optimization**:

- Tree-shaking and dead code elimination
- Code splitting by route and component
- Lazy loading of images, components, and routes
- Bundle compression and minification
- Critical CSS inlining
- Font subsetting and optimization
- Image optimization pipeline (WebP/AVIF, responsive srcset, lazy loading)

**Rendering Optimization**:

- Server-side rendering (SSR) or static site generation (SSG)
- Incremental static regeneration (ISR)
- Streaming server-side rendering
- Partial hydration (islands architecture)
- Virtual DOM diffing optimization
- Memoization (React.memo, useMemo, useCallback)

### Phase 5: Optimization Recommendations

For each issue, provide:

```
### [P0/P1/P2/P3] Issue Title

- **Category**: CPU / Memory / I/O / Network / Frontend
- **Severity**: P0 (blocking) / P1 (critical) / P2 (major) / P3 (minor)
- **Current performance**: measurement and baseline
- **Root cause**: why it is slow
- **Target performance**: goal for improvement
- **Recommendation**: specific change to make
- **Implementation details**:

\`\`\`language
// before and after code
\`\`\`

- **Expected improvement**: estimated gain
- **Effort**: Small / Medium / Large
- **Risk**: Low / Medium / High
```

### Phase 6: Verification

After implementing optimizations:

- Re-run benchmarks and compare to baselines
- Verify correctness (no behavior changes)
- Check for regressions in other areas
- Monitor in production (gradual rollout)
- Document optimizations for future reference

## Output Report

### Executive Summary
- Current state assessment
- Key bottlenecks identified
- Quick wins (high impact, low effort)
- Long-term recommendations

### Detailed Findings
...organized by priority...

### Before/After Comparison
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| p99 latency | 500ms | 120ms | 76% |
| RPS | 1000 | 4500 | 350% |
| LCP | 4.2s | 1.8s | 57% |

### Recommendations Priority Matrix
| Effort | High Impact | Low Impact |
|--------|-------------|------------|
| Low | Do first | Do if time |
| High | Strategic | Avoid |
