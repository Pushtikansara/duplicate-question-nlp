---
name: performance
description: Use when optimizing application performance. Covers profiling, caching, database optimization, CDN, and performance monitoring.
---

# Performance Skill

## Instructions

Performance optimization improves system responsiveness, throughput, and resource efficiency. It is a continuous process of measurement, analysis, and improvement. This skill covers performance profiling, caching strategies, database optimization, CDN usage, and performance monitoring in production.

### Performance Metrics

Understanding what to measure is the first step in performance optimization:

| Metric | Definition | Target |
|--------|------------|--------|
| Latency | Time to process a single request | p50 < 100ms, p99 < 500ms |
| Throughput | Requests processed per second | Varies by system |
| CPU Usage | Percentage of CPU capacity | Keep under 80% average |
| Memory Usage | RAM consumption | Keep under 80% average |
| I/O Operations | Disk read/write operations | Minimize wait time |
| Network Latency | Time for network round trip | < 50ms within region |
| Error Rate | Percentage of failed requests | < 0.1% target |
| Apdex | Application Performance Index | > 0.94 target |

### The Performance Optimization Process

1. **Measure**: Establish baseline metrics
2. **Identify**: Find bottlenecks using profiling
3. **Analyze**: Determine root cause of bottleneck
4. **Optimize**: Implement the fix
5. **Measure**: Verify improvement
6. **Repeat**: Continue until performance target is met

### Bottleneck Analysis

Common bottleneck locations:

| Layer | Common Issues | Profiling Tools |
|-------|---------------|-----------------|
| Frontend | Large bundles, blocking JS, unoptimized images | Lighthouse, WebPageTest |
| Network | High latency, bandwidth limits | Chrome DevTools Network tab |
| Backend | Slow algorithms, N+1 queries, sync I/O | cProfile, XHProf, async-profiler |
| Database | Missing indexes, full table scans, lock contention | `EXPLAIN ANALYZE`, pg_stat_statements |
| Cache | Low hit rate, cache stampede | Redis monitoring, cache stats |
| Infrastructure | CPU saturation, memory pressure, disk IOPS | CloudWatch, Datadog, Prometheus |

## Examples

### Example 1: Web Performance Optimization

```html
<!-- Performance optimization checklist for web applications -->

<!DOCTYPE html>
<html lang="en">
<head>
    <!-- 1. Critical CSS inlined -->
    <style>
        /* Above-the-fold styles only */
        header { display: flex; }
        .hero { min-height: 80vh; }
    </style>

    <!-- 2. Preload critical resources -->
    <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="/hero.webp" as="image">

    <!-- 3. Preconnect to third-party origins -->
    <link rel="preconnect" href="https://api.example.com">
    <link rel="dns-prefetch" href="https://analytics.example.com">

    <!-- 4. Defer non-critical CSS -->
    <link rel="preload" href="/styles.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="/styles.css"></noscript>

    <!-- 5. Resource hints -->
    <link rel="prefetch" href="/next-page.html">
    <link rel="prerender" href="/likely-next-page.html">
</head>
<body>
    <!-- 6. Defer non-critical images -->
    <img src="placeholder.jpg" data-src="actual-image.webp" loading="lazy" width="800" height="600">

    <!-- 7. Async/defer scripts -->
    <script defer src="/app.js"></script>
    <script async src="/analytics.js"></script>

    <!-- 8. Intersection Observer for lazy loading -->
    <script>
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
    }
    </script>
</body>
</html>
```

```javascript
// JavaScript performance optimizations

// 1. Debounce expensive functions
function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

// 2. Throttle for rate-limited operations
function throttle(fn, limit = 100) {
    let inThrottle = false;
    return (...args) => {
        if (!inThrottle) {
            fn(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 3. Virtual scrolling for long lists
class VirtualScroller {
    constructor(container, items, itemHeight, renderItem) {
        this.container = container;
        this.items = items;
        this.itemHeight = itemHeight;
        this.renderItem = renderItem;
        this.visibleItems = Math.ceil(container.clientHeight / itemHeight) + 2;

        container.addEventListener('scroll', () => this.update());
        this.update();
    }

    update() {
        const scrollTop = this.container.scrollTop;
        const startIndex = Math.floor(scrollTop / this.itemHeight);
        const endIndex = Math.min(startIndex + this.visibleItems, this.items.length);

        // Only render visible items + buffer
        const visibleData = this.items.slice(startIndex, endIndex);
        // ... render visibleData
    }
}

// 4. Avoid layout thrashing (batch DOM reads and writes)
// Bad: alternating reads and writes
// element.style.width = '100px';
// const width = element.offsetWidth;

// Good: batch reads, then batch writes
const rects = elements.map(el => el.getBoundingClientRect());
elements.forEach((el, i) => {
    el.style.width = `${rects[i].width * 2}px`;
});

// 5. Use requestAnimationFrame for visual updates
function animate() {
    // Update animation state
    requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

// 6. Web Workers for CPU-intensive tasks
const worker = new Worker('processor.js');
worker.postMessage({ data: largeDataSet });
worker.onmessage = (event) => {
    console.log('Processed:', event.data);
};

// 7. Code splitting (dynamic imports)
const handleClick = async () => {
    const module = await import('./heavy-module.js');
    module.showDialog();
};

// 8. Cache DOM queries
const $header = document.querySelector('.header'); // Cache this

// 9. Use passive event listeners for scroll/touch
document.addEventListener('touchstart', handler, { passive: true });

// 10. Optimize loops
// Prefer for loops over forEach for large arrays
for (let i = 0; i < items.length; i++) {
    // process items[i]
}
```

### Example 2: Database Query Optimization

```sql
-- 1. Use EXPLAIN ANALYZE to understand query plans
EXPLAIN ANALYZE
SELECT p.*, COUNT(o.id) as order_count
FROM products p
LEFT JOIN orders o ON o.product_id = p.id
WHERE p.category_id = 5
  AND p.price > 50
GROUP BY p.id
ORDER BY order_count DESC
LIMIT 20;

-- 2. Add appropriate indexes
-- For the query above:
CREATE INDEX idx_products_category_price ON products (category_id, price);
CREATE INDEX idx_orders_product_id ON orders (product_id);

-- 3. Partial indexes for filtered queries
CREATE INDEX idx_orders_active ON orders (created_at)
WHERE status IN ('pending', 'processing');

-- 4. Covering indexes for index-only scans
CREATE INDEX idx_products_listing ON products (category_id, price, status)
INCLUDE (name, image_url);

-- 5. Avoid SELECT *
-- BAD:
SELECT * FROM users WHERE id = 1;

-- GOOD:
SELECT id, name, email FROM users WHERE id = 1;

-- 6. Use EXISTS instead of COUNT for existence checks
-- BAD:
IF (SELECT COUNT(*) FROM orders WHERE user_id = 1) > 0

-- GOOD:
IF EXISTS (SELECT 1 FROM orders WHERE user_id = 1)

-- 7. Pagination with keyset (cursor-based)
-- BAD (OFFSET is slow for large offsets):
SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 100000;

-- GOOD (keyset pagination):
SELECT * FROM products WHERE id > 100000 ORDER BY id LIMIT 20;

-- 8. Materialized views for expensive aggregations
CREATE MATERIALIZED VIEW daily_sales_summary AS
SELECT
    date_trunc('day', created_at) as sale_date,
    product_id,
    COUNT(*) as order_count,
    SUM(amount) as total_revenue
FROM orders
WHERE status = 'completed'
GROUP BY date_trunc('day', created_at), product_id;

REFRESH MATERIALIZED VIEW daily_sales_summary;

-- 9. Batch operations instead of row-by-row
-- BAD (N queries):
-- foreach order: UPDATE orders SET status = 'processed' WHERE id = ?;

-- GOOD (single query):
UPDATE orders SET status = 'processed'
WHERE id = ANY($1::int[]);

-- 10. Use connection pooling
-- Configure PgBouncer or similar for connection reuse
```

### Example 3: Caching Strategy

```typescript
/**
 * Multi-level caching strategy.
 */

interface CacheConfig {
    ttl: number;           // Time to live in seconds
    maxSize: number;       // Maximum items in cache
    namespace: string;     // Cache namespace for isolation
}

interface CacheEntry<T> {
    data: T;
    expiresAt: number;
    createdAt: number;
}

// Level 1: In-memory cache (fastest)
class MemoryCache<T> {
    private cache: Map<string, CacheEntry<T>> = new Map();
    private readonly config: CacheConfig;

    constructor(config: CacheConfig) {
        this.config = config;
    }

    get(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) return null;

        if (Date.now() > entry.expiresAt) {
            this.cache.delete(key);
            return null;
        }

        return entry.data;
    }

    set(key: string, data: T): void {
        if (this.cache.size >= this.config.maxSize) {
            // Evict oldest entry
            const oldest = this.cache.keys().next().value;
            this.cache.delete(oldest);
        }

        this.cache.set(key, {
            data,
            expiresAt: Date.now() + this.config.ttl * 1000,
            createdAt: Date.now(),
        });
    }

    invalidate(key: string): void {
        this.cache.delete(key);
    }

    invalidatePattern(pattern: string): void {
        const regex = new RegExp(pattern);
        for (const key of this.cache.keys()) {
            if (regex.test(key)) this.cache.delete(key);
        }
    }

    clear(): void {
        this.cache.clear();
    }

    get size(): number {
        return this.cache.size;
    }
}

// Level 2: Redis cache (shared across instances)
class RedisCache<T> {
    constructor(
        private redis: any, // Redis client
        private config: CacheConfig
    ) {}

    async get(key: string): Promise<T | null> {
        const fullKey = `${this.config.namespace}:${key}`;
        const data = await this.redis.get(fullKey);
        if (!data) return null;
        return JSON.parse(data);
    }

    async set(key: string, data: T): Promise<void> {
        const fullKey = `${this.config.namespace}:${key}`;
        await this.redis.setex(fullKey, this.config.ttl, JSON.stringify(data));
    }

    async invalidate(key: string): Promise<void> {
        const fullKey = `${this.config.namespace}:${key}`;
        await this.redis.del(fullKey);
    }

    async invalidatePattern(pattern: string): Promise<void> {
        const fullPattern = `${this.config.namespace}:${pattern}`;
        const keys = await this.redis.keys(fullPattern);
        if (keys.length > 0) {
            await this.redis.del(...keys);
        }
    }
}

// Level 3: CDN cache (edge caching)
// Configured at the CDN level (CloudFront, Cloudflare, etc.)

// Cache-aside pattern (lazy loading)
class DataService<T> {
    constructor(
        private memoryCache: MemoryCache<T>,
        private redisCache: RedisCache<T>,
        private fetchFromDb: (key: string) => Promise<T>
    ) {}

    async get(key: string): Promise<T> {
        // Level 1: Check memory cache
        const memoryResult = this.memoryCache.get(key);
        if (memoryResult) {
            console.log('Cache hit (memory)');
            return memoryResult;
        }

        // Level 2: Check Redis cache
        const redisResult = await this.redisCache.get(key);
        if (redisResult) {
            console.log('Cache hit (redis)');
            // Populate memory cache
            this.memoryCache.set(key, redisResult);
            return redisResult;
        }

        // Level 3: Fetch from database
        console.log('Cache miss - fetching from DB');
        const data = await this.fetchFromDb(key);

        // Populate both caches
        this.memoryCache.set(key, data);
        await this.redisCache.set(key, data);

        return data;
    }

    async invalidate(key: string): Promise<void> {
        this.memoryCache.invalidate(key);
        await this.redisCache.invalidate(key);
    }
}

// Cache stampede prevention
class CacheStampedePrevention {
    private locks = new Map<string, Promise<any>>();

    async getOrCompute<T>(
        key: string,
        compute: () => Promise<T>,
        ttlMs: number
    ): Promise<T> {
        // Try cache first
        const cached = await this.getFromCache(key);
        if (cached) return cached;

        // Check if another request is already computing
        const existing = this.locks.get(key);
        if (existing) return existing;

        // Compute and cache
        const promise = compute().then(async (result) => {
            await this.setCache(key, result, ttlMs);
            this.locks.delete(key);
            return result;
        }).catch((error) => {
            this.locks.delete(key);
            throw error;
        });

        this.locks.set(key, promise);
        return promise;
    }
}
```

### Example 4: API Performance Optimization

```typescript
/**
 * API performance optimization patterns.
 */

import express from 'express';
import compression from 'compression';
import helmet from 'helmet';

const app = express();

// 1. Enable compression
app.use(compression({
    level: 6,               // Balance speed and compression
    threshold: 1024,        // Only compress responses > 1KB
    filter: (req, res) => {
        if (req.headers['x-no-compression']) return false;
        return compression.filter(req, res);
    },
}));

// 2. Add caching headers
app.get('/api/products', async (req, res) => {
    // Cache for 60 seconds on CDN, 30 seconds on browser
    res.set('Cache-Control', 'public, max-age=30, s-maxage=60');
    res.set('Surrogate-Control', 'max-age=60');

    // ETag for conditional requests
    const data = await getProducts();
    const etag = crypto.createHash('md5').update(JSON.stringify(data)).digest('hex');

    if (req.headers['if-none-match'] === etag) {
        return res.status(304).end(); // Not modified
    }

    res.set('ETag', etag);
    res.json(data);
});

// 3. Response pagination
app.get('/api/orders', async (req, res) => {
    const page = parseInt(req.query.page as string) || 1;
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const offset = (page - 1) * limit;

    const { rows, count } = await getOrders(limit, offset);

    res.json({
        data: rows,
        pagination: {
            page,
            limit,
            total: count,
            totalPages: Math.ceil(count / limit),
            hasNext: offset + limit < count,
            hasPrev: page > 1,
        },
    });
});

// 4. Field selection (sparse fields)
app.get('/api/users/:id', async (req, res) => {
    const fields = (req.query.fields as string)?.split(',') || ['id', 'name', 'email'];
    const user = await getUser(req.params.id, fields);

    if (!user) return res.status(404).json({ error: 'Not found' });

    // Only return requested fields
    const result = {};
    fields.forEach(field => {
        if (user[field] !== undefined) result[field] = user[field];
    });

    res.json(result);
});

// 5. Batch endpoint
app.post('/api/batch', async (req, res) => {
    const { requests } = req.body;

    if (!Array.isArray(requests) || requests.length > 20) {
        return res.status(400).json({ error: 'Invalid batch request' });
    }

    const results = await Promise.all(
        requests.map(async ({ method, path, body }) => {
            try {
                // Simulate internal routing
                const result = await routeInternal(method, path, body);
                return { status: 200, body: result };
            } catch (error) {
                return { status: error.status || 500, body: { error: error.message } };
            }
        })
    );

    res.json(results);
});

// 6. Request timeout
app.use((req, res, next) => {
    res.setTimeout(30000, () => {
        res.status(503).json({ error: 'Request timeout' });
    });
    next();
});

// 7. Rate limiting
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
    windowMs: 60 * 1000,    // 1 minute
    max: 100,                // 100 requests per minute
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests, please try again later.' },
});

app.use('/api/', limiter);

// 8. Connection pooling for database
import { Pool } from 'pg';

const pool = new Pool({
    max: 20,               // Maximum connections in pool
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
});

// 9. Query optimization with prepared statements
const getUserQuery = {
    name: 'get-user-by-id',
    text: 'SELECT id, name, email FROM users WHERE id = $1',
};

async function getUserById(id: number) {
    const result = await pool.query(getUserQuery, [id]);
    return result.rows[0];
}

// 10. Response streaming for large datasets
app.get('/api/export', async (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Transfer-Encoding', 'chunked');

    const stream = await createExportStream();
    stream.pipe(res);
});
```

### Example 5: CDN and Asset Optimization

```typescript
/**
 * CDN and static asset optimization.
 */

import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import sharp from 'sharp';   // Image optimization
import { minify } from 'terser';  // JS minification
import cssnano from 'cssnano';     // CSS minification

interface AssetConfig {
    bucket: string;
    region: string;
    cdnDomain: string;
}

class AssetOptimizer {
    private s3: S3Client;
    private config: AssetConfig;

    constructor(config: AssetConfig) {
        this.config = config;
        this.s3 = new S3Client({ region: config.region });
    }

    // Image optimization pipeline
    async optimizeImage(
        inputBuffer: Buffer,
        options: {
            widths: number[];         // Responsive widths
            formats: string[];        // ['webp', 'avif', 'jpeg']
            quality?: number;          // 1-100
        }
    ): Promise<string[]> {
        const urls: string[] = [];

        for (const width of options.widths) {
            for (const format of options.formats) {
                const optimized = await sharp(inputBuffer)
                    .resize(width, undefined, {
                        fit: 'inside',
                        withoutEnlargement: true,
                    })
                    [format]({
                        quality: options.quality || 80,
                        effort: 6, // Maximum compression effort
                    })
                    .toBuffer();

                const key = `images/${width}/${Date.now()}.${format}`;

                await this.s3.send(new PutObjectCommand({
                    Bucket: this.config.bucket,
                    Key: key,
                    Body: optimized,
                    ContentType: `image/${format}`,
                    CacheControl: 'public, max-age=31536000, immutable',
                }));

                urls.push(`${this.config.cdnDomain}/${key}`);
            }
        }

        return urls;
    }

    // JavaScript optimization
    async optimizeJavaScript(
        code: string,
        filename: string
    ): Promise<{ optimized: string; sourceMap: string }> {
        const result = await minify({
            [filename]: code,
        }, {
            compress: {
                drop_console: true,       // Remove console.log
                drop_debugger: true,
                passes: 3,                // Multiple compression passes
                unsafe: false,
                pure_funcs: ['console.log'],
            },
            mangle: {
                toplevel: true,
                reserved: ['$', 'require', 'exports', 'import'],
            },
            output: {
                comments: false,
                beautify: false,
            },
            sourceMap: {
                url: `${filename}.map`,
            },
        });

        await this.s3.send(new PutObjectCommand({
            Bucket: this.config.bucket,
            Key: `js/${filename}`,
            Body: result.code,
            ContentType: 'application/javascript',
            CacheControl: 'public, max-age=31536000, immutable',
        }));

        if (result.map) {
            // Upload source map (private, for debugging)
            await this.s3.send(new PutObjectCommand({
                Bucket: this.config.bucket,
                Key: `js/${filename}.map`,
                Body: result.map,
                ContentType: 'application/json',
            }));
        }

        return {
            optimized: result.code,
            sourceMap: result.map?.toString() || '',
        };
    }

    // Generate responsive image HTML
    generatePictureHtml(
        baseUrl: string,
        alt: string,
        widths: number[],
        formats: string[] = ['avif', 'webp', 'jpeg']
    ): string {
        const sources = formats.map(format => `
            <source
                type="image/${format}"
                srcset="${widths.map(w =>
                    `${baseUrl}/${format}/${w}.${format} ${w}w`
                ).join(', ')}"
                sizes="(max-width: 768px) 100vw, 50vw"
            >
        `).join('\n');

        return `
            <picture>
                ${sources}
                <img
                    src="${baseUrl}/jpeg/${widths[0]}.jpeg"
                    alt="${alt}"
                    loading="lazy"
                    decoding="async"
                    width="${widths[0]}"
                    height="auto"
                >
            </picture>
        `;
    }
}
```

### Example 6: Performance Monitoring

```typescript
/**
 * Performance monitoring and alerting.
 */

interface PerformanceMetric {
    name: string;
    value: number;
    tags: Record<string, string>;
    timestamp: Date;
}

class PerformanceMonitor {
    private metrics: PerformanceMetric[] = [];
    private readonly alertThresholds: Map<string, number> = new Map();

    constructor() {
        // Define alert thresholds
        this.alertThresholds.set('api.latency.p99', 500);   // 500ms
        this.alertThresholds.set('api.error_rate', 1);       // 1%
        this.alertThresholds.set('db.query_time', 200);       // 200ms
        this.alertThresholds.set('cache.hit_rate', 90);       // 90%
    }

    // Collect metrics
    recordMetric(name: string, value: number, tags: Record<string, string> = {}): void {
        this.metrics.push({
            name,
            value,
            tags,
            timestamp: new Date(),
        });

        // Check alert thresholds
        this.checkThreshold(name, value);
    }

    // Time an operation
    async timeOperation<T>(
        name: string,
        operation: () => Promise<T>,
        tags: Record<string, string> = {}
    ): Promise<T> {
        const start = performance.now();
        try {
            const result = await operation();
            const duration = performance.now() - start;
            this.recordMetric(name, duration, { ...tags, status: 'success' });
            return result;
        } catch (error) {
            const duration = performance.now() - start;
            this.recordMetric(name, duration, { ...tags, status: 'error' });
            throw error;
        }
    }

    // Check thresholds and alert
    private checkThreshold(name: string, value: number): void {
        const threshold = this.alertThresholds.get(name);
        if (threshold && value > threshold) {
            this.sendAlert({
                metric: name,
                value,
                threshold,
                severity: value > threshold * 2 ? 'critical' : 'warning',
                timestamp: new Date(),
            });
        }
    }

    // Send alert (to PagerDuty, Slack, etc.)
    private sendAlert(alert: {
        metric: string;
        value: number;
        threshold: number;
        severity: string;
        timestamp: Date;
    }): void {
        console.warn(`ALERT: ${alert.severity} - ${alert.metric} = ${alert.value} (threshold: ${alert.threshold})`);
        // Send to alerting system...
    }

    // Calculate percentiles
    private percentile(values: number[], p: number): number {
        const sorted = [...values].sort((a, b) => a - b);
        const index = Math.ceil((p / 100) * sorted.length) - 1;
        return sorted[Math.max(0, Math.min(index, sorted.length - 1))];
    }

    // Get dashboard data
    getDashboardData(timeRangeMs: number = 60000): any {
        const recent = this.metrics.filter(
            m => Date.now() - m.timestamp.getTime() < timeRangeMs
        );

        const latencies = recent
            .filter(m => m.name.endsWith('.latency'))
            .map(m => m.value);

        return {
            timeRange: `${timeRangeMs / 1000}s`,
            requestCount: recent.filter(m => m.name.startsWith('api')).length,
            errorCount: recent.filter(m => m.tags.status === 'error').length,
            averageLatency: latencies.reduce((a, b) => a + b, 0) / (latencies.length || 1),
            p95Latency: this.percentile(latencies, 95),
            p99Latency: this.percentile(latencies, 99),
            cacheHitRate: this.calculateCacheHitRate(recent),
        };
    }
}

// Usage
const monitor = new PerformanceMonitor();

async function handleRequest(req: Request, res: Response) {
    const result = await monitor.timeOperation(
        'api.request',
        () => processRequest(req),
        { path: req.path, method: req.method }
    );

    monitor.recordMetric('api.request_size', req.body?.length || 0);
    monitor.recordMetric('api.response_size', JSON.stringify(result).length);
}
```

### Example 7: Database Performance Tuning

```sql
-- PostgreSQL performance tuning

-- 1. Check for slow queries
SELECT queryid, query, calls,
       total_time / calls as avg_time,
       rows,
       shared_blks_hit,
       shared_blks_read
FROM pg_stat_statements
WHERE calls > 100
ORDER BY total_time DESC
LIMIT 20;

-- 2. Monitor index usage
SELECT schemaname, tablename, indexname,
       idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- Unused indexes
ORDER BY tablename;

-- 3. Find table bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename))) as total_size,
       pg_size_pretty(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename))) as table_size,
       pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename))
           - pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename))) as index_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)) DESC;

-- 4. Vacuum and analyze
VACUUM (VERBOSE, ANALYZE) table_name;
ANALYZE table_name;

-- 5. Configure work_mem for sort operations
-- SET work_mem = '256MB';  -- Per sort operation
-- SET maintenance_work_mem = '1GB';  -- For VACUUM, CREATE INDEX

-- 6. Check long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       query, state
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - pg_stat_activity.query_start > interval '5 minutes'
ORDER BY duration DESC;

-- 7. Partition large tables
CREATE TABLE orders_partitioned (
    id BIGSERIAL,
    customer_id BIGINT NOT NULL,
    order_date DATE NOT NULL,
    amount DECIMAL(12,2)
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_q1 PARTITION OF orders_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

-- 8. Use BRIN indexes for time-series data
CREATE INDEX idx_orders_date_brin ON orders USING BRIN (order_date)
    WITH (pages_per_range = 32);
```

## Best Practices

### Measurement First

- Always establish baseline metrics before making changes
- Profile in production or production-like environments
- Use percentile-based metrics (p50, p95, p99) not just averages
- Set up continuous performance monitoring
- Create performance budgets and enforce them in CI

### Caching Strategy

- Use multi-level caching (in-memory → Redis → CDN)
- Set appropriate TTLs based on data freshness requirements
- Implement cache invalidation patterns (cache-aside, write-through)
- Prevent cache stampede with locking or early recomputation
- Monitor cache hit rates and adjust strategies accordingly

### Database Optimization

- Index based on query patterns, not table structure
- Use `EXPLAIN ANALYZE` before and after optimization
- Implement query timeout to prevent runaway queries
- Use connection pooling to reduce connection overhead
- Consider read replicas for read-heavy workloads
- Partition large tables for better maintenance and query performance

### Frontend Optimization

- Minimize bundle size through code splitting and tree shaking
- Optimize images (responsive sizes, modern formats, lazy loading)
- Use CDN for static assets
- Implement PRPL pattern (Push, Render, Pre-cache, Lazy-load)
- Use performance budgets and Lighthouse CI

## Common Mistakes

- **Optimizing without measuring**: Making changes without data leads to wasted effort on the wrong bottlenecks.
- **Premature optimization**: Optimizing code before it is proven to be a bottleneck adds complexity without benefit.
- **Ignoring the database**: Most performance problems are database-related. Start with query optimization before application changes.
- **Caching everything**: Caching adds complexity and stale data risks. Cache only what needs to be cached.
- **Not monitoring in production**: Development environments do not reflect production traffic patterns and data volumes.
- **Missing slow queries**: Without monitoring slow queries, database performance degrades silently.
- **Over-indexing**: Too many indexes slow down write operations. Review and remove unused indexes.
- **Not using CDN**: Serving static assets directly from the application server wastes bandwidth and increases latency.
- **Ignoring N+1 queries**: One query that triggers N additional queries is a common and expensive pattern.
- **Forgetting about mobile**: Desktop performance does not equal mobile performance. Test on real mobile devices.

## Libraries

### Profiling Tools

| Tool | Language | Purpose |
|------|----------|---------|
| perf | Linux | CPU profiling and tracing |
| Valgrind | C/C++ | Memory profiling |
| async-profiler | Java | Low-overhead Java profiling |
| Py-Spy | Python | Sampling Python profiler |
| clinic.js | Node.js | Comprehensive Node.js profiling |
| XHProf | PHP | PHP profiling |
| dotMemory | .NET | .NET memory profiling |

### Monitoring and APM

| Tool | Purpose |
|------|---------|
| Datadog | Full-stack monitoring and APM |
| New Relic | Application performance monitoring |
| Prometheus + Grafana | Open-source metrics and dashboards |
| Sentry | Error tracking and performance |
| Elastic APM | Open-source APM solution |
| AWS X-Ray | Distributed tracing for AWS |
| Jaeger | Open-source distributed tracing |

### Web Performance

| Tool | Purpose |
|------|---------|
| Lighthouse | Web page performance auditing |
| WebPageTest | Advanced web performance testing |
| Sitespeed.io | Web performance CI tool |
| PageSpeed Insights | Google's page speed tool |
| BundlePhobia | Bundle size analysis |
| Webpack Bundle Analyzer | Bundle composition visualization |

## Design Principles

### Measure First, Optimize Second

Every optimization should be driven by data. Without measurements, you are guessing at bottlenecks. Profile in production conditions, establish baselines, and verify improvements with the same measurements.

### Bottleneck Principle

The throughput of a system is limited by its slowest component (the bottleneck). Optimizing any other component does not improve overall throughput. Find the bottleneck, fix it, then find the next one.

### Caching is Not Free

Caching introduces complexity, stale data risks, and memory overhead. Only cache data that is expensive to compute and is accessed frequently. Monitor cache hit rates and invalidate aggressively.

### Performance is a Feature

Treat performance as a feature that must be actively maintained, not something to fix when it becomes a problem. Set performance budgets, monitor metrics in CI, and include performance in the definition of done.

## Coding Standards

### Performance Monitoring Setup

```
monitoring/
  metrics/                  # Metric definitions
    api_metrics.ts
    database_metrics.ts
  dashboards/               # Grafana dashboard JSON
    api-performance.json
    database-performance.json
  alerts/                   # Alert configurations
    latency-alerts.yml
    error-rate-alerts.yml
```

### Performance Budget

```json
{
    "budgets": [
        {
            "resourceType": "script",
            "budget": 300
        },
        {
            "resourceType": "image",
            "budget": 200
        },
        {
            "resourceType": "total",
            "budget": 500
        },
        {
            "timing": {
                "metric": "interactive",
                "budget": 5000
            }
        },
        {
            "timing": {
                "metric": "first-contentful-paint",
                "budget": 2000
            }
        }
    ]
}
```
