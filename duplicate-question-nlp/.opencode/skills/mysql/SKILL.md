---
name: mysql
description: Use when working with MySQL. Covers SQL, indexing, query optimization, replication, and configuration.
---

# MySQL Skill

## Instructions

MySQL is one of the most widely used open-source relational database management systems. This skill covers SQL writing, schema design, indexing, query optimization, replication configuration, and server administration for MySQL (including MariaDB-compatible syntax where applicable).

### Connection and Basic Usage

Connect to a MySQL server using the `mysql` command-line client:

```bash
mysql -h hostname -P 3306 -u username -p database_name
```

Execute SQL statements interactively or through application connectors (mysql2, MySQL Connector/Python, PDO, etc.). Always use prepared statements with parameterized queries to prevent SQL injection.

### SQL Writing Conventions

- Use uppercase for SQL keywords (SELECT, INSERT, UPDATE, DELETE, etc.)
- Use lowercase with underscores for table and column names
- End all statements with a semicolon
- Use backticks to quote identifiers that are reserved words or contain special characters
- Use `EXPLAIN` or `EXPLAIN FORMAT=JSON` to analyze query execution plans
- Avoid MySQL-specific extensions unless portability is not required

### Schema Design

- Use InnoDB as the storage engine for production workloads (supports transactions, foreign keys, row-level locking)
- Use `BIGINT UNSIGNED AUTO_INCREMENT` or `UUID()` for primary keys
- Prefer `VARCHAR` over `CHAR` for variable-length strings
- Use `DATETIME` for general date/time storage; use `TIMESTAMP` if you need automatic timezone conversion
- Choose `DECIMAL(precision, scale)` for exact numeric values like monetary amounts
- Use `TINYINT(1)` for boolean columns (MySQL does not have a native BOOLEAN type)
- Define `NOT NULL` with appropriate defaults to avoid NULL complications
- Limit `TEXT` and `BLOB` column usage as they are stored off-page
- Use foreign key constraints with InnoDB for referential integrity

### Indexing Strategy

- Create indexes on columns used in WHERE, JOIN, ORDER BY, and GROUP BY clauses
- Use composite indexes when queries filter by multiple columns; order columns by selectivity
- Understand the leftmost prefix rule: queries must use the leftmost columns in a composite index
- Use `EXPLAIN` to verify index usage; look for `type` = `ref` or `range` instead of `ALL`
- Prefer `B-Tree` indexes for most workloads; use `HASH` indexes only for MEMORY tables
- Use `FULLTEXT` indexes for full-text search on MyISAM or InnoDB tables (MySQL 5.6+)
- Use `SPATIAL` indexes for geometric data types
- Consider descending indexes (MySQL 8.0+) for columns sorted in DESC order
- Use `INVISIBLE` indexes (MySQL 8.0+) to test impact of dropping an index without removing it
- Monitor index usage with `performance_schema.table_io_waits_summary_by_index_usage`
- Avoid over-indexing; each index increases write overhead

### Query Optimization

- Use `EXPLAIN FORMAT=JSON` for detailed query plan analysis
- Optimize JOINs by ensuring join columns are indexed on both sides
- Use `LIMIT` with `OFFSET` for pagination but consider keyset pagination for large offsets
- Avoid `SELECT *` in production; specify only required columns
- Use `EXISTS` instead of `IN` for subqueries when checking existence
- Use `UNION ALL` instead of `UNION` when duplicates are acceptable
- Leverage derived tables (subqueries in FROM clause) for complex aggregations
- Use window functions (MySQL 8.0+) for analytical queries instead of session variables
- Optimize `GROUP BY` by indexing the grouping columns
- Set `sql_mode` to `ONLY_FULL_GROUP_BY` to enforce ANSI SQL compliance
- Configure `innodb_buffer_pool_size` to hold working data set in memory

### Configuration and Tuning

- Set `innodb_buffer_pool_size` to 70-80% of available RAM for dedicated database servers
- Configure `innodb_log_file_size` for write-heavy workloads (typically 1-2GB)
- Set `max_connections` appropriately; use connection pooling instead of high connection counts
- Enable `slow_query_log` to identify queries exceeding `long_query_time`
- Configure `query_cache_type = 0` (query cache deprecated in MySQL 8.0)
- Set `innodb_flush_log_at_trx_commit = 1` for ACID compliance; use 2 for better performance
- Configure `sort_buffer_size` and `join_buffer_size` appropriately per session
- Set `tmp_table_size` and `max_heap_table_size` for memory-optimized temporary tables
- Use `performance_schema` and `sys` schema for monitoring and diagnostics

### Replication

- Use GTID-based replication (MySQL 5.6+) for easier failover management
- Configure row-based binary logging for consistency: `binlog_format = ROW`
- Set `expire_logs_days` or `binlog_expire_logs_seconds` to manage binary log retention
- Use semi-synchronous replication for improved data durability
- Configure replica read-only to prevent accidental writes
- Monitor replication lag with `SHOW REPLICA STATUS`
- Use multi-source replication to consolidate data from multiple primaries
- Implement group replication for multi-primary or single-primary high availability
- Consider using MySQL InnoDB Cluster for automated group replication and failover

### Administration

- Perform regular backups with `mysqldump` for logical backups or `xtrabackup` for physical backups
- Test restore procedures in a non-production environment
- Use `mysqlcheck` for table maintenance (check, repair, analyze, optimize)
- Monitor slow query log to identify performance bottlenecks
- Set up `pt-query-digest` (Percona Toolkit) for query analysis
- Configure `max_allowed_packet` for large BLOB or TEXT data transfers
- Regularly update MySQL and apply security patches
- Use `mysql_secure_installation` post-installation to improve default security

## Examples

### Example 1: Creating an Optimized Table

```sql
CREATE TABLE orders (
    id BIGINT UNSIGNED AUTO_INCREMENT,
    customer_id BIGINT UNSIGNED NOT NULL,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') NOT NULL DEFAULT 'pending',
    shipping_address TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_order_date (order_date),
    INDEX idx_status_date (status, order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Example 2: Composite Index Usage

```sql
-- Create a composite index
CREATE INDEX idx_user_status_date ON orders (customer_id, status, order_date);

-- Queries that can fully use the index:
SELECT * FROM orders WHERE customer_id = 123 AND status = 'pending' ORDER BY order_date;

-- Query that partially uses the index (only customer_id):
SELECT * FROM orders WHERE customer_id = 123;

-- Query that cannot use the index (skips leftmost column):
-- SELECT * FROM orders WHERE status = 'pending'; -- Full scan on status
```

### Example 3: Recursive CTE for Hierarchical Data

```sql
WITH RECURSIVE category_path AS (
    SELECT id, name, parent_id, 1 AS level
    FROM categories
    WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, cp.level + 1
    FROM categories c
    INNER JOIN category_path cp ON c.parent_id = cp.id
)
SELECT * FROM category_path ORDER BY level, name;
```

### Example 4: Window Functions for Analytics

```sql
SELECT
    product_id,
    sale_date,
    revenue,
    SUM(revenue) OVER (PARTITION BY product_id ORDER BY sale_date) AS running_total,
    AVG(revenue) OVER (PARTITION BY product_id ORDER BY sale_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7d,
    LAG(revenue, 1) OVER (PARTITION BY product_id ORDER BY sale_date) AS prev_day_revenue
FROM daily_sales;
```

### Example 5: EXPLAIN Analysis

```sql
EXPLAIN FORMAT=JSON
SELECT c.name, COUNT(o.id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE c.created_at > '2024-01-01'
GROUP BY c.id
ORDER BY order_count DESC
LIMIT 10;
```

### Example 6: Setting Up a Read Replica

```sql
-- On primary
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='replica_host',
    SOURCE_USER='replication_user',
    SOURCE_PASSWORD='secure_password',
    SOURCE_LOG_FILE='mysql-bin.000001',
    SOURCE_LOG_POS=123456;
START REPLICA;

-- On replica
SHOW REPLICA STATUS\G
```

### Example 7: Using JSON Data Type

```sql
CREATE TABLE product_attributes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT UNSIGNED NOT NULL,
    attributes JSON NOT NULL,
    INDEX idx_product_id (product_id)
);

INSERT INTO product_attributes (product_id, attributes) VALUES
(1, '{"color": "red", "size": "M", "weight": 0.5}');

-- Query JSON fields
SELECT product_id,
    JSON_EXTRACT(attributes, '$.color') AS color,
    attributes->>'$.size' AS size
FROM product_attributes
WHERE JSON_CONTAINS(attributes, '"red"', '$.color');
```

## Best Practices

### Development Practices

- Use migration tools (Flyway, Liquibase, Alembic) for schema versioning
- Always test queries with production-scale data volumes in staging
- Enforce proper SQL modes: `sql_mode = STRICT_TRANS_TABLES, ONLY_FULL_GROUP_BY`
- Use meaningful aliases in queries for readability
- Implement query timeout at the application level
- Use `mysqlslap` for load testing query performance
- Store configuration values in tables rather than application constants for runtime changes
- Use views to provide abstraction layers over complex queries

### Performance Practices

- Configure `innodb_buffer_pool_size` appropriately (70-80% of RAM for DB servers)
- Ensure `innodb_file_per_table = 1` for better space management
- Adjust `innodb_io_capacity` and `innodb_io_capacity_max` based on storage subsystem
- Use `ANALYZE TABLE` periodically to update table statistics
- Consider partitioning large tables (MySQL 5.7+)
- Use `OPTIMIZE TABLE` during maintenance windows for heavily fragmented tables
- Configure `thread_cache_size` to reduce connection overhead
- Use `innodb_read_io_threads` and `innodb_write_io_threads` for parallel I/O

### Security Practices

- Always use parameterized queries or prepared statements to prevent SQL injection
- Create application-specific users with least-privilege access
- Use `mysql_native_password` or `caching_sha2_password` for authentication
- Configure SSL/TLS for client-server connections
- Set `validate_password` plugin for strong password policies
- Limit user access to specific IP ranges in `GRANT` statements
- Regular security audits with `mysql_audit`
- Never use root credentials in application configuration
- Encrypt sensitive data using `AES_ENCRYPT`/`AES_DECRYPT` at application level

## Common Mistakes

- **Using MyISAM instead of InnoDB**: MyISAM lacks transactions, foreign keys, and row-level locking. InnoDB is the recommended storage engine for virtually all production workloads.
- **Ignoring the slow query log**: Many performance issues go unnoticed without monitoring slow queries. Always enable and review the slow query log.
- **Over-indexing**: Creating indexes on every column increases write overhead and storage. Each index must be updated on every INSERT, UPDATE, and DELETE.
- **Not using `EXPLAIN`**: Deploying queries without analyzing their execution plans leads to unexpected performance degradation as data grows.
- **Using `OFFSET` for deep pagination**: OFFSET causes MySQL to scan and discard rows, becoming progressively slower. Use keyset pagination (WHERE id > last_seen) for large datasets.
- **Setting `max_connections` too high without connection pooling**: High connection counts consume memory and CPU. Use a connection pooler like ProxySQL.
- **Using deprecated features**: Query cache, MyISAM, and `PASSWORD()` function are deprecated or removed in MySQL 8.0.
- **Ignoring character set and collation**: Mixing different charset/collation across tables causes inefficient query plans and data conversion issues.
- **Forgetting to optimize JOIN queries**: Unindexed join columns cause full table scans and massive performance degradation on joined tables.
- **Not monitoring replication lag**: Replication lag can cause stale reads on replicas and potential data loss during failover.

## Libraries

### MySQL Connectors and ORMs

| Language | Driver/ORM | Notes |
|----------|-----------|-------|
| Node.js | mysql2, mysqljs, Prisma, Sequelize, TypeORM | mysql2 supports prepared statements natively |
| Python | mysql-connector-python, PyMySQL, SQLAlchemy, Django ORM | SQLAlchemy is production-proven |
| Go | go-sql-driver/mysql, GORM, sqlx | go-sql-driver/mysql is the reference driver |
| Java | MySQL Connector/J, Hibernate, jOOQ, MyBatis | Connector/J is the official Oracle driver |
| PHP | PDO_MySQL, mysqli, Laravel Eloquent | PDO is portable across database systems |
| Ruby | mysql2 gem, ActiveRecord, Sequel | mysql2 gem is the modern Ruby driver |
| .NET | MySQL Connector/NET, Entity Framework Core | Use Pomelo.EntityFrameworkCore.MySql for EF Core |

### Administration and Monitoring Tools

| Tool | Purpose |
|------|---------|
| MySQL Workbench | Official GUI for schema design, query development, and administration |
| phpMyAdmin | Web-based database administration |
| Percona Toolkit | Advanced command-line tools (pt-query-digest, pt-online-schema-change) |
| ProxySQL | High-performance connection pooler and query router |
| Orchestrator | MySQL replication topology management and failover |
| Prometheus + mysqld_exporter | Metrics collection and monitoring |
| MySQL Shell | Advanced client with X DevAPI, admin API, and scripting |

## Design Principles

### Defensive Schema Design

Design schemas that enforce constraints at the database level. Applications come and go, but data integrity must be guaranteed by the database. Use NOT NULL, UNIQUE, CHECK, and FOREIGN KEY constraints liberally.

### Minimal Data Movement

Queries should process the minimum amount of data necessary. Filter early in the query pipeline to reduce intermediate result sets. Use indexes to access only the pages needed.

### Consistency over Performance

For transactional systems, prioritize data consistency over raw performance. Use `innodb_flush_log_at_trx_commit = 1` for ACID compliance. Sacrificing durability for speed can lead to data corruption or loss.

### Configuration as Code

Database configuration should be version-controlled alongside application code. Use infrastructure-as-code tools (Ansible, Terraform, Chef) to manage MySQL configuration consistently across environments.

## Coding Standards

### Naming Conventions

- Tables: `snake_case` plural (e.g., `order_items`, `user_sessions`)
- Columns: `snake_case` (e.g., `first_name`, `created_at`)
- Primary key: `id` (or `table_name_id` for composite PKs)
- Foreign key: `referenced_table_singular_id` (e.g., `customer_id`)
- Indexes: `idx_table_col1_col2`
- Unique constraints: `uq_table_column`
- Foreign key constraints: `fk_table_referenced_table`
- Stored procedures: `sp_description`
- Triggers: `trg_table_action`

### SQL Formatting

```sql
-- Consistent formatting
SELECT
    c.id,
    c.name,
    COUNT(o.id) AS order_count,
    SUM(o.total) AS total_revenue
FROM customers c
    INNER JOIN orders o ON o.customer_id = c.id
WHERE
    c.active = 1
    AND o.order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY
    c.id,
    c.name
HAVING
    COUNT(o.id) > 5
ORDER BY
    total_revenue DESC
LIMIT 20;
```

### Comment Style

- Use `-- ` for line comments in migration scripts
- Document the purpose of complex queries at the top
- Add comments to triggers and stored procedures explaining the business logic
- Use `COMMENT ON TABLE` and `COMMENT ON COLUMN` for metadata documentation

### Migration Standards

- One logical change per migration file
- Sequential numbering: `001_create_users.sql`, `002_add_email_index.sql`
- Always include rollback scripts
- Never modify a deployed migration; create a new migration to reverse or modify
- Test migrations against a copy of production data
