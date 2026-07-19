---
name: postgresql
description: Use when working with PostgreSQL. Covers SQL, indexing, query optimization, partitioning, replication, and administration.
---

# PostgreSQL Skill

## Instructions

PostgreSQL is a powerful, open-source object-relational database system with a strong reputation for reliability, feature robustness, and performance. This skill provides guidance on writing efficient SQL, designing schemas, optimizing queries, and managing PostgreSQL databases.

### Connection and Basic Usage

Connect to a PostgreSQL database using the `psql` command-line client:

```bash
psql -h hostname -p 5432 -U username -d database_name
```

Execute SQL statements directly from the CLI or through application drivers (libpq, pgx, node-postgres, psycopg2, etc.). Always use parameterized queries to prevent SQL injection.

### SQL Writing Conventions

- Use uppercase for SQL keywords (SELECT, FROM, WHERE, INSERT, etc.)
- Use lowercase for column names, table names, and aliases
- Use descriptive names for constraints, indexes, and sequences
- End all SQL statements with a semicolon
- Use `EXPLAIN ANALYZE` to understand query execution plans
- Prefer `BIGSERIAL` over `SERIAL` for auto-incrementing primary keys to avoid running out of IDs
- Use `TIMESTAMPTZ` instead of `TIMESTAMP` to handle time zone information correctly

### Schema Design

- Normalize data to at least Third Normal Form (3NF) unless performance requirements dictate denormalization
- Use `UUID` or `BIGSERIAL` as primary keys; avoid natural keys that may change
- Define foreign key constraints to maintain referential integrity
- Use `CHECK` constraints for data validation at the database level
- Prefer `TEXT` or `VARCHAR` over fixed-length `CHAR(n)` for string columns
- Use `NUMERIC(precision, scale)` for monetary values to avoid floating-point errors
- Create composite types and enumerations where appropriate for domain modeling
- Use `GENERATED ALWAYS AS ... STORED` for computed columns

### Indexing Strategy

- Create indexes on columns used in `WHERE`, `JOIN`, `ORDER BY`, and `GROUP BY` clauses
- Use `EXPLAIN ANALYZE` to verify index usage
- Prefer B-tree indexes for equality and range queries
- Use GiST or GIN indexes for full-text search, array containment, and geometric data
- Use BRIN indexes on large tables where data is naturally ordered (e.g., time-series data)
- Create covering indexes with `INCLUDE` columns to support index-only scans
- Avoid over-indexing; each index adds overhead on write operations
- Use `CREATE INDEX CONCURRENTLY` for production environments to avoid table locks
- Monitor index usage with `pg_stat_user_indexes` and remove unused indexes
- Consider partial indexes (`WHERE` clause) for frequently filtered subsets of data

### Query Optimization

- Write queries that filter as early as possible in the execution plan
- Use `JOIN LATERAL` for complex subqueries that reference outer query columns
- Prefer `EXISTS` over `IN` for subquery existence checks
- Use `UNION ALL` instead of `UNION` when duplicates are acceptable
- Avoid `SELECT *` in production code; specify only needed columns
- Use Common Table Expressions (CTEs) for readability but be aware they act as optimization fences
- Materialize expensive CTEs explicitly when needed
- Use `OFFSET` with `ORDER BY` for pagination; prefer keyset pagination for large datasets
- Leverage `pg_stat_statements` to identify slow queries
- Use `VACUUM` and `ANALYZE` regularly to maintain query planner statistics

### Partitioning

- Use declarative partitioning (built-in since PostgreSQL 10) for large tables
- Choose partitioning strategy: `RANGE`, `LIST`, or `HASH` based on query patterns
- Ensure partition keys align with common query filters
- Partition pruning should eliminate irrelevant partitions at query planning time
- Create indexes on each partition individually; global indexes are not supported
- Use `PG_PARTMAN` extension for automated partition management
- Monitor partition sizes and add new partitions proactively

### Replication and High Availability

- Use streaming replication for read replicas and failover
- Configure `synchronous_commit` for data durability vs. performance trade-offs
- Use `pgBouncer` or `pgpool-II` for connection pooling
- Implement automated failover with Patroni, repmgr, or Stolon
- Monitor replication lag with `pg_stat_replication`
- Use logical replication for selective data replication and cross-version upgrades
- Set up `wal_level = logical` for change data capture (CDC) use cases

### Administration

- Regular backups with `pg_dump` for logical backups and `pg_basebackup` for physical backups
- Test restore procedures periodically
- Configure `postgresql.conf` for workload-specific performance tuning
- Use `pg_hba.conf` for client authentication control
- Monitor database size, bloat, and connection count
- Set up `log_min_duration_statement` to capture slow queries
- Use `pg_rewind` to quickly restore a failed primary after split-brain scenarios
- Keep PostgreSQL version up to date for security and performance improvements

## Examples

### Example 1: Creating a Partitioned Table

```sql
CREATE TABLE orders (
    id BIGSERIAL,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMPTZ NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    status TEXT NOT NULL
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

CREATE INDEX idx_orders_customer_id ON orders (customer_id);
```

### Example 2: Optimized Pagination with Keyset

```sql
-- Instead of:
SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 100000;

-- Use keyset pagination:
SELECT * FROM products
WHERE id > 100000
ORDER BY id
LIMIT 20;
```

### Example 3: Full-Text Search

```sql
ALTER TABLE articles ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', title), 'A') ||
        setweight(to_tsvector('english', body), 'B')
    ) STORED;

CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);

SELECT title, ts_rank(search_vector, query) AS rank
FROM articles, to_tsquery('english', 'postgreSQL & performance') query
WHERE search_vector @@ query
ORDER BY rank DESC;
```

### Example 4: Recursive CTE for Hierarchical Data

```sql
WITH RECURSIVE org_tree AS (
    SELECT id, name, parent_id, 1 AS depth
    FROM employees
    WHERE id = 1
    UNION ALL
    SELECT e.id, e.name, e.parent_id, ot.depth + 1
    FROM employees e
    INNER JOIN org_tree ot ON e.parent_id = ot.id
)
SELECT * FROM org_tree ORDER BY depth, name;
```

### Example 5: Window Functions for Analytical Queries

```sql
SELECT
    department_id,
    employee_name,
    salary,
    AVG(salary) OVER (PARTITION BY department_id) AS dept_avg,
    salary - AVG(salary) OVER (PARTITION BY department_id) AS diff_from_avg,
    RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank
FROM employees;
```

### Example 6: Using JOIN LATERAL

```sql
SELECT c.name, recent_orders.order_date, recent_orders.total
FROM customers c
LEFT JOIN LATERAL (
    SELECT order_date, total
    FROM orders
    WHERE customer_id = c.id
    ORDER BY order_date DESC
    LIMIT 3
) recent_orders ON true
WHERE c.active = true;
```

### Example 7: Concurrent Index Creation

```sql
CREATE INDEX CONCURRENTLY idx_orders_status_date
ON orders (status, order_date)
WHERE status IN ('pending', 'processing');

-- After confirming the index is valid:
DROP INDEX CONCURRENTLY idx_orders_old_index;
```

## Best Practices

### Development Practices

- Use migration-based schema management (e.g., Sqitch, Flyway, or Alembic)
- Write idempotent migration scripts that can be applied multiple times safely
- Always test queries with realistic data volumes before deploying to production
- Use a consistent naming convention: `snake_case` for tables, columns, indexes
- Name indexes descriptively: `idx_tablename_columnname`
- Name constraints: `fk_tablename_referencedtable`, `uq_tablename_column`
- Use schemas for logical separation within a database
- Set `statement_timeout` at the session or role level to prevent runaway queries
- Use `pgTAP` for database unit testing
- Implement row-level security (RLS) for multi-tenant applications

### Performance Practices

- Configure `shared_buffers` to 25% of total RAM for dedicated database servers
- Set `work_mem` appropriately for complex sorts and hash operations
- Enable `jit` for complex analytical queries but disable for OLTP workloads
- Use connection pooling to manage connection overhead
- Set `random_page_cost` to 1.1 for SSD storage
- Disable `synchronous_commit` for workloads that can tolerate small data loss windows
- Use `pg_prewarm` extension to preload frequently accessed data into cache
- Monitor `checkpoint` frequency and adjust `max_wal_size` and `min_wal_size`

### Security Practices

- Use `pg_hba.conf` with specific host, user, and database restrictions
- Create application-specific roles with minimal required privileges
- Use `GRANT` only on specific tables, not at the database level
- Encrypt connections using SSL/TLS with `sslmode=verify-full`
- Enable `log_statement = 'ddl'` and audit DDL changes
- Regularly apply security patches and minor version updates
- Never store plain-text passwords; use `pgcrypto` extensions for hashing
- Implement `row_level_security` for fine-grained access control

## Common Mistakes

- **Missing indexes on foreign key columns**: Foreign key columns are not automatically indexed. Without an index, cascading deletes and joins cause sequential scans on the referencing table.
- **Over-indexing**: Creating too many indexes on a table slows down INSERT, UPDATE, and DELETE operations. Each index must be maintained during write operations.
- **Using `SELECT *` in production**: This fetches all columns, causing unnecessary I/O and preventing index-only scans. Always specify required columns.
- **Neglecting `VACUUM` and `ANALYZE`**: Without regular vacuuming, dead tuples accumulate, causing table bloat and degraded query performance.
- **Using `OFFSET` for deep pagination**: OFFSET skips rows by scanning and discarding them, which becomes increasingly slow for large offsets. Use keyset pagination instead.
- **Ignoring connection pooling**: Each PostgreSQL connection consumes considerable resources. Without pooling, connection overhead can saturate the database.
- **Not using `EXPLAIN ANALYZE`**: Guessing why a query is slow without analyzing the execution plan leads to ineffective optimization.
- **Using `TIMESTAMP` instead of `TIMESTAMPTZ`**: Storing timestamps without time zone information leads to incorrect time calculations across different time zones.
- **Forgetting to set `search_path`**: Relying on the default search path can cause ambiguous table references and security vulnerabilities.
- **Running long transactions**: Long-running transactions block vacuum and can cause transaction ID wraparound issues.

## Libraries

### PostgreSQL Drivers and ORMs

| Language | Driver/ORM | Notes |
|----------|-----------|-------|
| Python | psycopg2, asyncpg, SQLAlchemy, Django ORM | psycopg2 is the most mature; asyncpg for async |
| Node.js | node-postgres (pg), Prisma, Sequelize, Knex | pg is low-level; Prisma provides type safety |
| Go | pgx, lib/pq, GORM, sqlx | pgx is the performance-focused choice |
| Rust | sqlx, diesel, tokio-postgres | sqlx provides compile-time checked queries |
| Java | JDBC, Hibernate, jOOQ, MyBatis | jOOQ generates typesafe SQL from database schema |
| Ruby | pg gem, ActiveRecord, Sequel | Sequel is lighter than ActiveRecord |
| C/C++ | libpq, libpqxx | libpq is the official C client library |

### PostgreSQL Extensions

| Extension | Purpose |
|-----------|---------|
| pg_stat_statements | Track execution statistics of all SQL statements |
| pgcrypto | Cryptographic functions for hashing and encryption |
| PostGIS | Geographic information system (GIS) support |
| pg_partman | Automated partition management |
| pg_repack | Remove table bloat without locks |
| pg_hint_plan | Force query planner to use specific plans |
| pgaudit | Detailed audit logging |
| uuid-ossp | UUID generation functions |
| hstore | Key-value store within PostgreSQL |
| pg_trgm | Trigram text matching for fuzzy search |

## Design Principles

### Data Integrity First

PostgreSQL enforces ACID compliance rigorously. Design schemas that leverage database-level constraints (foreign keys, CHECK constraints, NOT NULL, UNIQUE) rather than relying solely on application-level validation. This prevents data corruption even when applications have bugs.

### Schema as API

Treat the database schema as a public API. Changes to tables, columns, or constraints should follow a deprecation process. Use views to provide backward-compatible interfaces when restructuring tables.

### Single Source of Truth

Data should exist in exactly one place in normalized form. Avoid duplicating data across tables unless performance requirements explicitly demand denormalization with documented synchronization mechanisms.

### Least Privilege Security

Database roles should have the minimum permissions necessary. Application roles should not own tables; use separate migration roles with schema modification permissions.

### Index with Intent

Every index should have a documented purpose (which queries it serves). Index blindly created "just in case" add maintenance overhead and should be periodically reviewed and removed if unused.

## Coding Standards

### Naming Conventions

- Tables: `plural_snake_case` (e.g., `order_items`, `user_profiles`)
- Columns: `singular_snake_case` (e.g., `first_name`, `created_at`)
- Primary key: `id` for single-column PKs
- Foreign key: `<referenced_table_singular>_id` (e.g., `customer_id`, `product_id`)
- Indexes: `idx_<table>_<columns>` (e.g., `idx_orders_customer_date`)
- Unique constraints: `uq_<table>_<columns>` (e.g., `uq_users_email`)
- Foreign key constraints: `fk_<table>_<referenced>` (e.g., `fk_orders_customers`)
- Sequences: `<table>_<column>_seq` (e.g., `orders_id_seq`)

### Code Structure

```sql
-- SQL Statement Ordering
SELECT columns                    -- 1. Select columns
FROM tables                       -- 2. Source tables
JOIN other_tables ON conditions   -- 3. Joins
WHERE conditions                  -- 4. Filter rows
GROUP BY columns                  -- 5. Group rows
HAVING conditions                 -- 6. Filter groups
ORDER BY columns                  -- 7. Order results
LIMIT n OFFSET m;                 -- 8. Paginate
```

### Comment Style

- Use `COMMENT ON` statements for table and column documentation
- Write inline SQL comments for complex logic with `--`
- Document non-obvious indexes with comments explaining which queries they serve
- Include migration changelogs in version-controlled migration scripts

### Migration Standards

- One change per migration file
- Number migrations sequentially (e.g., `001_add_customers_table.sql`)
- Always provide both `up` and `down` migrations
- Test rollback procedures
- Never modify a committed migration; create a new one to reverse changes
