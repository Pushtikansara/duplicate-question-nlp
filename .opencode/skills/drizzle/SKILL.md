---
name: drizzle
description: Use when working with Drizzle ORM. Covers schema definition, queries, migrations, and SQL-like API.
---

# Drizzle Skill

## Instructions

Drizzle ORM is a lightweight, type-safe ORM for TypeScript and Node.js that follows SQL closely. Unlike traditional ORMs that abstract away SQL, Drizzle embraces SQL's syntax and patterns while providing compile-time type safety and auto-completion. It supports PostgreSQL, MySQL, SQLite, and Turso (libSQL). This skill covers schema definition, query building, migrations, and best practices.

### Project Setup

Install Drizzle ORM and the database driver:

```bash
# PostgreSQL
npm install drizzle-orm pg
npm install -D @types/pg

# MySQL
npm install drizzle-orm mysql2
npm install -D @types/mysql2

# SQLite
npm install drizzle-orm better-sqlite3
npm install -D @types/better-sqlite3

# Drizzle Kit (migrations)
npm install -D drizzle-kit
```

### Schema Definition

Define your database schema as TypeScript code using Drizzle's schema helpers. This approach keeps your schema in sync with your application code and provides type safety.

```typescript
import { pgTable, serial, varchar, timestamp, integer, boolean, jsonb } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email', { length: 255 }).notNull().unique(),
    name: varchar('name', { length: 100 }),
    age: integer('age'),
    isActive: boolean('is_active').default(true),
    metadata: jsonb('metadata'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull().$onUpdate(() => new Date()),
});
```

### Query Building

Drizzle provides a SQL-like query builder that feels familiar to SQL users:

```typescript
import { db } from './db';
import { users } from './schema';
import { eq, and, or, gte, lte, like, desc } from 'drizzle-orm';

// SELECT with filtering
const activeUsers = await db.select()
    .from(users)
    .where(and(eq(users.isActive, true), gte(users.age, 18)))
    .orderBy(desc(users.createdAt))
    .limit(10);

// INSERT
const newUser = await db.insert(users).values({
    email: 'user@example.com',
    name: 'John Doe',
    age: 30,
}).returning();

// UPDATE
await db.update(users)
    .set({ name: 'Jane Doe' })
    .where(eq(users.id, 1));

// DELETE
await db.delete(users).where(eq(users.id, 1));
```

### Migrations with Drizzle Kit

Drizzle Kit is the CLI tool for managing database migrations:

```bash
# Generate migration from schema changes
npx drizzle-kit generate:pg --name add_users_table

# Apply migrations
npx drizzle-kit push:pg

# Drop and recreate (DEV only)
npx drizzle-kit drop

# Studio (GUI database browser)
npx drizzle-kit studio
```

Drizzle's migration approach is schema-first: you define your schema in TypeScript, then generate migration SQL files from schema diffs.

## Examples

### Example 1: Complete Schema with Relations

```typescript
import { pgTable, serial, varchar, text, integer, timestamp, boolean, foreignKey, uniqueIndex, index } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// Tables
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email', { length: 255 }).notNull().unique(),
    name: varchar('name', { length: 100 }),
    roleId: integer('role_id').references(() => roles.id),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull().$onUpdate(() => new Date()),
}, (table) => ({
    emailIdx: uniqueIndex('email_idx').on(table.email),
    roleIdx: index('role_idx').on(table.roleId),
}));

export const posts = pgTable('posts', {
    id: serial('id').primaryKey(),
    title: varchar('title', { length: 255 }).notNull(),
    content: text('content'),
    published: boolean('published').default(false),
    authorId: integer('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
    createdAt: timestamp('created_at').defaultNow().notNull(),
});

export const roles = pgTable('roles', {
    id: serial('id').primaryKey(),
    name: varchar('name', { length: 50 }).notNull().unique(),
});

// Relations
export const usersRelations = relations(users, ({ one, many }) => ({
    posts: many(posts),
    role: one(roles, {
        fields: [users.roleId],
        references: [roles.id],
    }),
}));

export const postsRelations = relations(posts, ({ one }) => ({
    author: one(users, {
        fields: [posts.authorId],
        references: [users.id],
    }),
}));

export const rolesRelations = relations(roles, ({ many }) => ({
    users: many(users),
}));
```

### Example 2: Complex Queries with Joins and Subqueries

```typescript
import { db } from './db';
import { users, posts, roles } from './schema';
import { eq, and, gte, desc, count, sql } from 'drizzle-orm';

// JOIN query
const result = await db.select({
    userId: users.id,
    userName: users.name,
    postId: posts.id,
    postTitle: posts.title,
    roleName: roles.name,
})
.from(users)
.leftJoin(posts, eq(posts.authorId, users.id))
.leftJoin(roles, eq(users.roleId, roles.id))
.where(eq(users.isActive, true))
.orderBy(desc(posts.createdAt));

// Aggregation with GROUP BY
const userPostCounts = await db.select({
    userId: users.id,
    userName: users.name,
    postCount: count(posts.id),
})
.from(users)
.leftJoin(posts, eq(posts.authorId, users.id))
.groupBy(users.id, users.name)
.having(gte(count(posts.id), 5));

// Subquery
const recentPosts = db.select()
    .from(posts)
    .where(gte(posts.createdAt, new Date('2024-01-01')))
    .as('recent_posts');

const activeUsersWithRecentPosts = await db.select()
    .from(users)
    .innerJoin(recentPosts, eq(users.id, recentPosts.authorId));
```

### Example 3: Prepared Statements for Performance

```typescript
import { db } from './db';
import { users } from './schema';
import { eq } from 'drizzle-orm';

// Prepare a statement for reuse
const getUserById = db.select()
    .from(users)
    .where(eq(users.id, sql.placeholder('id')))
    .prepare('get_user_by_id');

// Execute multiple times efficiently
const user1 = await getUserById.execute({ id: 1 });
const user2 = await getUserById.execute({ id: 2 });
const user3 = await getUserById.execute({ id: 3 });
```

### Example 4: Batch Operations

```typescript
import { db } from './db';
import { users } from './schema';

// Batch insert
const newUsers = await db.insert(users).values([
    { email: 'user1@example.com', name: 'User 1' },
    { email: 'user2@example.com', name: 'User 2' },
    { email: 'user3@example.com', name: 'User 3' },
]).returning();

// Batch update with case (using raw SQL helper)
await db.update(users)
    .set({ isActive: true })
    .where(eq(users.roleId, 1));
```

### Example 5: Transactions

```typescript
import { db } from './db';
import { users, posts } from './schema';
import { eq } from 'drizzle-orm';

await db.transaction(async (tx) => {
    const user = await tx.insert(users).values({
        email: 'new@example.com',
        name: 'New User',
    }).returning();

    await tx.insert(posts).values({
        title: 'First Post',
        content: 'Created in transaction',
        authorId: user[0].id,
    });

    // Rollback happens automatically on error
});
```

### Example 6: Raw SQL Queries

```typescript
import { db } from './db';
import { sql } from 'drizzle-orm';

// Execute raw SQL
const result = await db.execute(sql`
    SELECT u.*, COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON p.author_id = u.id
    GROUP BY u.id
    HAVING COUNT(p.id) > ${5}
`);

// Raw SQL with typed result
const users = await db.execute<{ id: number; name: string }>(sql`
    SELECT id, name FROM users WHERE is_active = ${true}
`);
```

### Example 7: Drizzle with SQLite (Turso)

```typescript
import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import { sqliteTable, integer, text } from 'drizzle-orm/sqlite-core';

const client = createClient({ url: 'file:./local.db' });
const db = drizzle(client);

export const todos = sqliteTable('todos', {
    id: integer('id').primaryKey({ autoIncrement: true }),
    title: text('title').notNull(),
    completed: integer('completed', { mode: 'boolean' }).default(false),
});

const allTodos = await db.select().from(todos).where(eq(todos.completed, false));
```

## Best Practices

### Schema Design

- Define schema in `src/db/schema.ts` for organization
- Use `pgTable`, `mysqlTable`, or `sqliteTable` based on your database
- Always use `sql.placeholder()` for prepared statements in production
- Define relations explicitly for type-safe joins
- Use enums with `pgEnum()` for fixed value sets
- Add indexes via the table definition's third argument
- Prefer `serial` or `uuid` for primary keys
- Use `$onUpdate()` hook for automatic timestamp updates

### Query Practices

- Use prepared statements (`prepare()`) for frequently executed queries
- Prefer `select({ ... })` over `select()` to limit fetched columns
- Use the `{ and, or, not }` operators for complex conditions
- Use `sql` template literal for database-specific SQL features
- Leverage Drizzle's type inference by using `typeof` and `InferModel`
- Use `returning()` with PostgreSQL for INSERT/UPDATE results
- Prefer relations API over manual joins for simpler queries

### Performance Practices

- Use prepared statements to avoid query parsing overhead
- Implement pagination with `limit()` and `offset()` or cursor-based
- Select only required columns to reduce data transfer
- Use batch inserts for multiple row creation
- Create appropriate indexes matching query patterns
- Monitor query performance with database-level tools
- Use connection pooling with drizzle-orm connection configuration

### Security Practices

- Always use parameterized queries (Drizzle does this by default)
- Never concatenate user input into SQL strings
- Use Zod or similar validation before passing data to Drizzle
- Implement row-level security at the database level for multi-tenant apps
- Sanitize ORDER BY and other dynamic query parts
- Use environment-specific database credentials

## Common Mistakes

- **Not using prepared statements**: Executing the same query shape repeatedly without preparation wastes database resources on query parsing.
- **Selecting all columns unnecessarily**: `db.select().from(table)` fetches all columns. Use `db.select({ col1: table.col1 })` to limit columns.
- **Missing relations definition**: Without explicit relations, type-safe joins are not available, and you lose IDE auto-completion on joined tables.
- **Not handling transactions for multi-step operations**: Multiple related writes should be wrapped in a transaction to maintain atomicity.
- **Using `.all()` on large result sets**: Loading all results into memory can exhaust resources for large datasets. Use pagination.
- **Ignoring database-specific features**: Each database has unique capabilities (e.g., PostgreSQL's JSONB). Use `sql` template literals to access them.
- **Not migrating before schema changes**: Changing schema directly without running drizzle-kit causes schema drift between code and database.
- **Forgetting `$onUpdate` for timestamps**: Without `$onUpdate`, updatedAt timestamps must be manually set on every update.
- **Using Drizzle with unsupported database features**: Not all SQL features are abstracted by Drizzle. Use raw SQL for database-specific features.
- **Mixing ORM paradigms**: Drizzle is SQL-first. Trying to use it like a traditional ORM (eager loading everything) defeats its purpose.

## Libraries

### Drizzle Ecosystem

| Library | Purpose |
|---------|---------|
| drizzle-orm | Core ORM with multi-database support |
| drizzle-kit | Schema migrations, push, and studio |
| drizzle-zod | Zod schema generation from Drizzle tables |
| drizzle-typebox | TypeBox schema generation from Drizzle tables |
| drizzle-valibot | Valibot schema generation from Drizzle tables |
| @drizzle-team/drizzle-studio | Database browsing GUI |

### Database Drivers

| Driver | Database | Notes |
|--------|----------|-------|
| pg (node-postgres) | PostgreSQL | Most popular PostgreSQL driver |
| @vercel/postgres | PostgreSQL | Vercel PostgreSQL integration |
| @neondatabase/serverless | PostgreSQL | Neon serverless PostgreSQL |
| mysql2 | MySQL | Modern MySQL driver with prepared statements |
| better-sqlite3 | SQLite | Synchronous SQLite driver |
| @libsql/client | Turso/libSQL | Edge SQLite-compatible database |
| bun:sqlite | SQLite | Bun's built-in SQLite binding |

## Design Principles

### SQL-First Philosophy

Drizzle does not hide SQL behind an abstraction layer. It embraces SQL's semantics and provides a type-safe TypeScript API that maps directly to SQL constructs. Write Drizzle code the same way you would write SQL: start with `select`, `insert`, `update`, or `delete`, then build up the query.

### Type Safety Without Magic

Drizzle generates types from your schema definitions at compile time. There is no code generation step required for type safety. The TypeScript compiler infers column types, relation types, and return types directly from your schema definition.

### Minimal Runtime Overhead

Drizzle is designed to be as thin as possible. Query building happens at the type level where possible, and at runtime Drizzle only constructs SQL strings with minimal processing. This makes it suitable for performance-critical and edge-computing environments.

### Database Portability with Intent

While Drizzle supports multiple database backends, it encourages users to be explicit about which database they are targeting. Schema helpers are database-specific (`pgTable`, `mysqlTable`, `sqliteTable`), making the target database clear in the code.

## Coding Standards

### File Organization

```
src/
  db/
    index.ts          # Database connection setup
    schema.ts          # All table definitions and relations
    migrations/        # Auto-generated migration files
    seed.ts           # Development seed data
```

### Naming Conventions

- Tables: `snake_case` plural (e.g., `user_profiles`, `order_items`)
- Columns: `snake_case` in the database (e.g., `first_name`, `created_at`)
- TypeScript identifiers: `camelCase` for variables, `PascalCase` for types
- Schema exports: export tables as plural nouns (e.g., `export const users = pgTable('users', ...)`)
- Relations: use `<table>Relations` naming (e.g., `usersRelations`)

### Query Structure

```typescript
// Chain methods vertically for readability
const result = await db
    .select({
        id: users.id,
        name: users.name,
        postCount: count(posts.id),
    })
    .from(users)
    .leftJoin(posts, eq(posts.authorId, users.id))
    .where(
        and(
            eq(users.isActive, true),
            gte(users.createdAt, startDate),
        )
    )
    .groupBy(users.id, users.name)
    .having(gte(count(posts.id), 1))
    .orderBy(desc(users.createdAt))
    .limit(20)
    .offset(0);
```

### Import Style

```typescript
// Prefer named imports for operators
import { eq, and, or, gte, lte, like, inArray, desc, asc, count, sql } from 'drizzle-orm';
import { pgTable, serial, varchar, integer, timestamp, boolean, jsonb, uuid, text, index, uniqueIndex } from 'drizzle-orm/pg-core';
// or mysql-core, sqlite-core respectively
```
