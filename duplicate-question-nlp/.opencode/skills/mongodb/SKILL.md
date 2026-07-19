---
name: mongodb
description: Use when working with MongoDB. Covers document modeling, aggregation pipeline, indexing, replication, and sharding.
---

# MongoDB Skill

## Instructions

MongoDB is a NoSQL document database designed for scalability and flexibility. It stores data in BSON documents, supports dynamic schemas, and provides powerful querying through the aggregation pipeline. This skill covers document modeling, query patterns, indexing strategies, replication, and sharding.

### Connection and Basic Usage

Connect to a MongoDB instance using the `mongosh` shell:

```bash
mongosh "mongodb://username:password@hostname:27017/database?replicaSet=rs0"
```

Use MongoDB drivers in your application language (Node.js, Python, Go, Java, etc.) with the native MongoDB API or ODM libraries (Mongoose, Prisma).

### Document Data Modeling

- Design documents based on how data is queried, not how it is stored relationally
- Embed related data that is accessed together (embedded documents and arrays)
- Reference data that is accessed independently or has unbounded growth
- Use document depth sparingly; MongoDB has a 100-level nesting limit
- Keep document size under 16MB (maximum BSON document size)
- Use appropriate BSON data types: ObjectId, Date, NumberLong, Decimal128, etc.
- Use arrays for one-to-many relationships when the array size is bounded
- Avoid overly deep nesting; prefer references for deeply hierarchical data
- Design for the read pattern: if reads always include subdocuments, embed them

### Query Patterns

- Use `find()` for basic queries with filter, projection, sort, limit, and skip
- Use cursor methods efficiently; avoid large in-memory sorts
- Use `countDocuments()` for estimated counts; `countDocuments()` for accurate counts
- Use `distinct()` for unique values across a collection
- Use `findOneAndUpdate()` for atomic read-modify-write operations
- Use `bulkWrite()` for batch operations when performance matters
- Prefer `$in` over multiple `$or` conditions for the same field
- Use `$expr` for queries that compare fields within the same document
- Use `$text` indexes for full-text search on string content

### Aggregation Pipeline

The aggregation pipeline is MongoDB's most powerful query feature. It processes documents through a pipeline of stages:

- `$match`: Filter documents early to reduce pipeline size
- `$project`: Reshape documents, include/exclude fields
- `$group`: Group documents for aggregation (SUM, AVG, MIN, MAX, PUSH, etc.)
- `$sort`: Sort documents within the pipeline
- `$lookup`: Perform left outer joins with another collection
- `$unwind`: Deconstruct arrays into individual documents
- `$bucket`/`$bucketAuto`: Group documents into buckets
- `$facet`: Run multiple pipelines within a single stage
- `$addFields`: Add new fields without explicitly including existing ones
- `$replaceRoot`: Replace the document root with a subdocument
- `$setWindowFields`: Perform window functions (MongoDB 5.0+)

Place `$match` and `$limit` stages early in pipelines to minimize data processing. Create indexes that support the aggregation pipeline.

### Indexing Strategy

- Create indexes for common query patterns, sorting operations, and aggregation stages
- Use single-field indexes for equality filters on one field
- Use compound indexes for queries filtering and sorting on multiple fields
- Use multikey indexes for array fields
- Use text indexes for full-text search
- Use geospatial indexes for location-based queries
- Use hashed indexes for hash-based sharding
- Use partial indexes to index only a subset of documents
- Use sparse indexes to index only documents that contain the indexed field
- Use TTL indexes for automatic document expiration
- Use wildcard indexes for queries against unknown field names
- Use case-insensitive indexes with collation

Follow the ESR (Equality, Sort, Range) rule for compound index field order:
1. Fields tested for equality first
2. Fields used for sorting next
3. Fields used for range queries last

### Replication

- Deploy replica sets with at least 3 data-bearing nodes (one primary, two secondaries)
- Use an arbiter only when necessary and never with an odd number of voting nodes
- Set `writeConcern: majority` for data durability in critical writes
- Set `readPreference: primaryPreferred` or `secondaryPreferred` for read scaling
- Monitor replication lag with `rs.printSlaveReplicationInfo()`
- Use `rs.stepDown()` for planned primary elections
- Configure oplog size based on workload; default is 5% of free disk space
- Use `rs.initiate()` for replica set initialization
- Use `rs.add()` to add members; `rs.remove()` to remove members
- Monitor Oplog window to ensure secondaries can catch up

### Sharding

- Choose shard key carefully; it determines data distribution and query efficiency
- Use hashed shard keys for even data distribution across shards
- Use ranged shard keys for queries that need to target specific shards
- Avoid monotonically increasing shard keys (they cause hot spots on one shard)
- Monitor chunk distribution with `sh.status()`
- Use `zone sharding` to pin data to specific shards based on geographic or other criteria
- Size your cluster: plan for 3x working set to fit in all shards' memory combined
- Use `balancer` to distribute chunks; schedule balancing during off-peak hours
- Ensure shard key is included in all queries to benefit from targeted queries
- Consider `compound shard keys` for balanced distribution and query efficiency

## Examples

### Example 1: Schema Design with Embedding vs. Referencing

```javascript
// Embedded design (for data accessed together, bounded size)
db.users.insertOne({
    _id: ObjectId(),
    username: "johndoe",
    profile: {
        firstName: "John",
        lastName: "Doe",
        avatar: "https://example.com/avatar.jpg"
    },
    addresses: [
        { type: "home", street: "123 Main St", city: "Springfield" },
        { type: "work", street: "456 Oak Ave", city: "Springfield" }
    ]
});

// Reference design (for data with unbounded growth)
db.posts.insertOne({
    _id: ObjectId(),
    userId: userId,
    title: "My First Post",
    content: "This is the content..."
});

db.comments.insertOne({
    postId: postId,
    userId: userId,
    text: "Great post!",
    createdAt: new Date()
});
```

### Example 2: Aggregation Pipeline for Order Analytics

```javascript
db.orders.aggregate([
    { $match: { status: "completed", orderDate: { $gte: ISODate("2024-01-01") } } },
    { $unwind: "$items" },
    {
        $group: {
            _id: "$items.category",
            totalRevenue: { $sum: { $multiply: ["$items.price", "$items.quantity"] } },
            totalItems: { $sum: "$items.quantity" },
            uniqueCustomers: { $addToSet: "$customerId" },
            avgOrderValue: { $avg: "$items.price" }
        }
    },
    { $sort: { totalRevenue: -1 } },
    {
        $lookup: {
            from: "categories",
            localField: "_id",
            foreignField: "categoryId",
            as: "categoryInfo"
        }
    },
    { $unwind: { path: "$categoryInfo", preserveNullAndEmptyArrays: true } },
    { $project: { _id: 0, category: "$categoryInfo.name", totalRevenue: 1, totalItems: 1, customerCount: { $size: "$uniqueCustomers" }, avgOrderValue: 1 } }
]);
```

### Example 3: Compound Index with ESR Rule

```javascript
// Query: find orders by customer (equality), sort by date (sort), filter by amount (range)
db.orders.createIndex({ customerId: 1, orderDate: -1, totalAmount: 1 });

// Index supports:
db.orders.find({ customerId: "abc123", totalAmount: { $gte: 100 } }).sort({ orderDate: -1 });
```

### Example 4: Change Streams for Real-time Events

```javascript
const changeStream = db.collection("orders").watch([
    { $match: { operationType: { $in: ["insert", "update"] } } }
]);

changeStream.on("change", (change) => {
    console.log("Order change detected:", change.documentKey);
    // Process the change event
});
```

### Example 5: Transactions (Multi-document ACID)

```javascript
const session = db.getMongo().startSession();
session.startTransaction();

try {
    const accounts = session.getDatabase("bank").accounts;
    accounts.updateOne({ _id: fromAccountId }, { $inc: { balance: -amount } });
    accounts.updateOne({ _id: toAccountId }, { $inc: { balance: amount } });
    session.commitTransaction();
} catch (error) {
    session.abortTransaction();
} finally {
    session.endSession();
}
```

### Example 6: Shard Key Selection

```javascript
// Good shard key: hashed for even distribution
sh.shardCollection("app.events", { eventId: "hashed" });

// Good compound shard key for query patterns
sh.shardCollection("app.orders", { customerId: 1, orderDate: 1 });

// Poor shard key: monotonically increasing
// sh.shardCollection("app.logs", { _id: 1 }); // Avoid
```

### Example 7: Aggregation with $setWindowFields

```javascript
db.sales.aggregate([
    { $match: { date: { $gte: ISODate("2024-01-01"), $lt: ISODate("2025-01-01") } } },
    {
        $setWindowFields: {
            partitionBy: "$region",
            sortBy: { date: 1 },
            output: {
                runningTotal: { $sum: "$amount", window: { documents: ["unbounded", "current"] } },
                movingAvg7: { $avg: "$amount", window: { documents: [-6, 0] } },
                rank: { $rank: {} }
            }
        }
    }
]);
```

## Best Practices

### Development Practices

- Use schema validation (JSON Schema) in MongoDB 3.6+ to enforce document structure
- Prefer the native MongoDB driver for maximum performance; use ODMs for productivity
- Always set a write concern on critical writes (majority)
- Use connection pooling in production applications
- Handle connection failures with retry logic
- Monitor slow queries with `db.setProfilingLevel(1, { slowms: 100 })`
- Use `explain("executionStats")` to analyze query performance
- Keep application-side pagination state to avoid large skips
- Use projection to return only needed fields
- Batch writes with bulkWrite for efficiency

### Performance Practices

- Ensure working set fits in memory for consistent performance
- Use compression (snappy or zlib) for storage savings with minimal CPU overhead
- Configure WiredTiger cache size appropriately (default is 50% of RAM minus 1GB)
- Monitor page faults; excessive page faults indicate insufficient memory
- Avoid large in-memory sorts; use indexes with sort operations
- Use covered queries (all required fields in the index) for fastest reads
- Use $hint to force index selection when the query planner chooses poorly
- Use $maxTimeMS() to limit query execution time
- Create indexes in the background for production deployments

### Security Practices

- Enable authentication with SCRAM, x.509, or LDAP
- Use TLS/SSL for all client-to-server and inter-node communication
- Create application-specific database users with minimal required roles
- Use role-based access control (RBAC) with built-in or custom roles
- Enable auditing to track database operations
- Restrict network access using firewalls and MongoDB IP whitelisting
- Encrypt data at rest using WiredTiger encryption or filesystem encryption
- Disable server-side JavaScript if not needed (security_JavaScriptEnabled)
- Regularly apply MongoDB security patches and version updates
- Use `db.isMaster()` to check if connected to a primary in production

## Common Mistakes

- **Poor document design**: Designing documents relationally instead of adapting to MongoDB's document model. Embed what is accessed together; reference what grows unboundedly.
- **No indexes on query patterns**: Running queries without proper indexes leads to collection scans. Use `explain()` to verify index usage.
- **Using `find()` with large `skip()`**: Large skip values force scanning through skipped documents. Use ranged queries with `$gt` or cursor-based pagination.
- **Unbounded array growth**: Pushing elements onto arrays that grow without bound leads to document migration overhead. Consider referencing for unbounded lists.
- **Ignoring write concern**: Using default write concern can cause data loss during primary elections. Use `w: majority` for important writes.
- **Poor shard key choice**: Using monotonically increasing shard keys creates hot spots. Use hashed or compound shard keys.
- **Not using aggregation pipeline efficiently**: Placing `$group` or `$sort` early without preceding `$match` causes unnecessary data processing.
- **Missing compound indexes**: Creating single-field indexes when queries filter by multiple fields forces scanning.
- **Large documents**: Exceeding 16MB BSON limit or having documents larger than necessary wastes memory and slows operations.
- **Insufficient oplog size**: Small oplog windows cause secondaries to fall out of sync and require resyncing.

## Libraries

### MongoDB Drivers and ODMs

| Language | Driver/ODM | Notes |
|----------|-----------|-------|
| Node.js | mongodb, Mongoose, Prisma, TypeORM | Mongoose provides schema validation |
| Python | pymongo, motor (async), MongoEngine, Beanie | motor is async; MongoEngine is ODM |
| Go | mongo-go-driver (official), mgo | Official driver is production-ready |
| Java | MongoDB Java Driver, Spring Data MongoDB, Morphia | Spring Data MongoDB integrates with Spring ecosystem |
| C# | MongoDB .NET Driver, C# Driver | Official .NET driver from MongoDB |
| Rust | mongodb (official), bson | Official driver with async support |
| Ruby | mongo (official driver), Mongoid | Mongoid provides ODM capabilities |

### MongoDB Tools

| Tool | Purpose |
|------|---------|
| mongosh | Modern MongoDB shell with scriptable API |
| MongoDB Compass | GUI for querying, visualizing, and optimizing |
| mongodump/mongorestore | Backup and restore utilities |
| mongoexport/mongoimport | JSON/CSV import and export |
| mongostat/mongotop | Real-time monitoring of database operations |
| mongos | Sharding router |
| Ops Manager | Enterprise management and automation |
| Atlas CLI | Command-line management for MongoDB Atlas |
| Percona Server for MongoDB | Alternative MongoDB-compatible server |
| mongolens | Query and index optimization tool |

## Design Principles

### Document Model Proximity

Store related data together. If your application always reads user data along with their recent orders, embed the order summary in the user document. The goal is to minimize the number of round trips to the database.

### Schema Flexibility with Constraints

While MongoDB supports dynamic schemas, production systems benefit from validation. Use JSON Schema validation, application-layer validation, or ODM schema definitions to enforce document structure.

### Data Locality

Design for read-heavy workloads by structuring documents to contain all data needed for a given view or query. This reduces the number of full document retrievals and leverages MongoDB's ability to return projections from indexes.

### Shard Key Awareness

The shard key determines all aspects of sharding performance. Design it based on the most common query patterns to enable targeted queries (broadcast queries touch all shards and are expensive).

## Coding Standards

### Naming Conventions

- Databases: `snake_case` (e.g., `ecommerce_production`)
- Collections: `plural_snake_case` (e.g., `user_profiles`, `order_items`)
- Fields: `camelCase` or `snake_case` consistently (e.g., `firstName` or `first_name`)
- Indexes: descriptive names (e.g., `idx_customerId_orderDate`)
- Avoid fields starting with `$` or containing `.` (reserved characters)

### Aggregation Pipeline Formatting

```javascript
db.collection.aggregate([
    { $match: { status: "active" } },
    { $group: { _id: "$category", count: { $sum: 1 } } },
    { $sort: { count: -1 } },
    { $limit: 10 }
]);
// Each stage on its own line
// Complex pipelines broken into stage variables
```

### Query Standards

- Always include `_id: 0` in projection when the `_id` field is not needed
- Use explicit projection to minimize returned data
- Use `const` or `let` for cursor variables and iterate explicitly
- Handle cursor iteration timeouts with `batchSize()` configuration
- Use `try/catch` blocks around write operations for error handling
- Comment complex aggregation stages explaining the transformation
