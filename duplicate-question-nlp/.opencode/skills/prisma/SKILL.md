---
name: prisma
description: Use when working with Prisma ORM. Covers schema design, migrations, queries, relations, and integration with frameworks.
---

# Prisma Skill

## Instructions

Prisma is a next-generation ORM that provides type-safe database access for Node.js, TypeScript, and Python applications. It consists of three main components: Prisma Migrate (schema migrations), Prisma Client (auto-generated query client), and Prisma Studio (GUI data browser). This skill covers schema modeling, migrations, query patterns, relation handling, and framework integration.

### Project Setup

Initialize Prisma in an existing project:

```bash
npm install prisma @prisma/client
npx prisma init
```

This creates a `prisma/schema.prisma` file and a `.env` file for database connection configuration.

### Schema Design (schema.prisma)

The Prisma schema file defines data sources, generators, and data models. It serves as the single source of truth for your database schema.

```prisma
datasource db {
  provider = "postgresql"  // or "mysql", "sqlite", "mongodb", "sqlserver", "cockroachdb"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
  //  binaryTargets = ["native"]  // for deployment targets
}
```

Define models that map to database tables:

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  posts     Post[]
  profile   Profile?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Field Types and Attributes

- Use appropriate scalar types: `String`, `Int`, `Float`, `Boolean`, `DateTime`, `Json`
- Use `BigInt` for large integer values
- Use `Bytes` for binary data
- Use `Unsupported()` for database-specific types not natively supported
- Attributes: `@id`, `@default()`, `@unique`, `@relation()`, `@updatedAt`
- For composite IDs, use `@@id([field1, field2])`
- For composite unique constraints, use `@@unique([field1, field2])`
- For indexes, use `@@index([field1, field2])`
- For full-text indexes on MySQL/PostgreSQL, use `@@fulltext([field1, field2])`

### Relations

Prisma supports three types of relations:

- **One-to-One**: Using `@relation` on one side with a unique foreign key
- **One-to-Many**: Using `@relation` on the many side with a foreign key
- **Many-to-Many**: Using implicit or explicit join tables

Define relations clearly:

```prisma
model User {
  id    Int    @id @default(autoincrement())
  posts Post[]
}

model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])
  authorId Int
}
```

### Migrations

Create and apply migrations to keep the database in sync with the schema:

```bash
# Create migration from schema changes
npx prisma migrate dev --name add_user_table

# Apply to production
npx prisma migrate deploy

# Reset database (DEV only)
npx prisma migrate reset

# Check migration status
npx prisma migrate status
```

Always review generated migration SQL before applying to production.

### Prisma Client Queries

```typescript
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

// Create
const user = await prisma.user.create({
  data: { email: "user@example.com", name: "John" }
})

// Read with filtering, pagination, and relations
const users = await prisma.user.findMany({
  where: { email: { contains: "example.com" } },
  include: { posts: true },
  orderBy: { createdAt: "desc" },
  take: 10,
  skip: 0
})

// Update
const updated = await prisma.user.update({
  where: { id: 1 },
  data: { name: "Jane" }
})

// Delete
await prisma.user.delete({ where: { id: 1 } })
```

### Framework Integration

Prisma integrates well with popular frameworks:

- **Next.js**: Use Prisma Client in API routes and Server Components
- **Express/Fastify**: Instantiate Prisma Client as a singleton middleware
- **NestJS**: Use the `@nestjs/prisma` module for dependency injection
- **GraphQL**: Combine with Nexus, TypeGraphQL, or Pothos for type-safe resolvers
- **tRPC**: Use Prisma types directly in tRPC routers

## Examples

### Example 1: Complete Schema with Relations

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  password  String
  role      Role     @default(USER)
  posts     Post[]
  profile   Profile?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("users")
}

model Profile {
  id        String @id @default(cuid())
  bio       String?
  avatarUrl String?
  userId    String @unique
  user      User   @relation(fields: [userId], references: [id])

  @@map("profiles")
}

model Post {
  id        String    @id @default(cuid())
  title     String
  content   String?
  published Boolean   @default(false)
  authorId  String
  author    User      @relation(fields: [authorId], references: [id])
  tags      Tag[]
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt

  @@index([authorId])
  @@map("posts")
}

model Tag {
  id    String @id @default(cuid())
  name  String @unique
  posts Post[]

  @@map("tags")
}

model PostTag {
  postId String
  tagId  String
  post   Post @relation(fields: [postId], references: [id])
  tag    Tag  @relation(fields: [tagId], references: [id])

  @@id([postId, tagId])
  @@map("post_tags")
}

enum Role {
  USER
  ADMIN
  MODERATOR
}
```

### Example 2: Complex Queries with Filtering, Pagination, and Aggregation

```typescript
const result = await prisma.post.findMany({
  where: {
    published: true,
    author: {
      role: { not: "ADMIN" }
    },
    tags: {
      some: {
        name: { in: ["typescript", "prisma"] }
      }
    },
    createdAt: {
      gte: new Date("2024-01-01"),
      lte: new Date("2024-12-31")
    }
  },
  select: {
    id: true,
    title: true,
    author: {
      select: {
        name: true,
        email: true
      }
    },
    tags: {
      select: {
        name: true
      }
    },
    _count: {
      select: {
        tags: true
      }
    }
  },
  orderBy: [
    { createdAt: "desc" },
    { title: "asc" }
  ],
  take: 20,
  skip: 0
});
```

### Example 3: Nested Write Operations

```typescript
// Create user with profile and posts
const user = await prisma.user.create({
  data: {
    email: "john@example.com",
    name: "John Doe",
    profile: {
      create: {
        bio: "Software developer",
        avatarUrl: "https://example.com/avatar.jpg"
      }
    },
    posts: {
      create: [
        { title: "First Post", content: "Hello world", published: true },
        { title: "Second Post", content: "Another post" }
      ]
    }
  },
  include: {
    profile: true,
    posts: true
  }
});

// Connect existing relations
const updatedPost = await prisma.post.update({
  where: { id: "postId123" },
  data: {
    tags: {
      connect: [{ id: "tagId1" }, { id: "tagId2" }]
    }
  }
});

// Disconnect and set operations
const post = await prisma.post.update({
  where: { id: "postId123" },
  data: {
    tags: {
      set: [{ id: "newTagId1" }]  // replaces all existing tags
    }
  }
});
```

### Example 4: Transactions

```typescript
// Interactive transaction
const result = await prisma.$transaction(async (tx) => {
  const user = await tx.user.create({
    data: { email: "new@example.com", name: "New User" }
  });

  const profile = await tx.profile.create({
    data: {
      bio: "New user profile",
      userId: user.id
    }
  });

  return { user, profile };
});

// Batch transaction
const [user1, user2] = await prisma.$transaction([
  prisma.user.update({ where: { id: 1 }, data: { name: "Alice" } }),
  prisma.user.update({ where: { id: 2 }, data: { name: "Bob" } })
]);

// With isolation level
await prisma.$transaction(
  [prisma.user.update({ ... })],
  { isolationLevel: "Serializable" }
);
```

### Example 5: Raw SQL Queries

```typescript
// Raw query with parameterized values
const users = await prisma.$queryRaw<User[]>`
  SELECT * FROM users WHERE email = ${email} AND active = ${true}
`;

// Raw execute
await prisma.$executeRaw`
  UPDATE users SET "lastLoginAt" = NOW() WHERE id = ${userId}
`;

// Raw with unsupported types (PostgreSQL)
const result = await prisma.$queryRawUnsafe<Array<{id: string}>>(
  'SELECT * FROM users WHERE metadata @> $1',
  JSON.stringify({ role: 'admin' })
);
```

### Example 6: Middleware and Extensions

```typescript
// Middleware for logging
prisma.$use(async (params, next) => {
  const start = Date.now();
  const result = await next(params);
  console.log(`Query ${params.model}.${params.action} took ${Date.now() - start}ms`);
  return result;
});

// Middleware for soft deletes
prisma.$use(async (params, next) => {
  if (params.model === 'User' && params.action === 'findMany') {
    if (!params.args) params.args = {};
    if (!params.args.where) params.args.where = {};
    params.args.where.deletedAt = null;
  }
  return next(params);
});

// Prisma Client extensions (Prisma 4+)
const xprisma = prisma.$extends({
  query: {
    user: {
      async findMany({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      }
    }
  },
  result: {
    user: {
      fullName: {
        needs: { firstName: true, lastName: true },
        compute(user) {
          return `${user.firstName} ${user.lastName}`;
        }
      }
    }
  }
});
```

### Example 7: Pagination with Cursors

```typescript
// First page
const page1 = await prisma.post.findMany({
  take: 20,
  orderBy: { id: "asc" }
});

const cursor = page1[page1.length - 1]?.id;

// Subsequent pages
const page2 = await prisma.post.findMany({
  take: 20,
  skip: 1, // Skip the cursor itself
  cursor: { id: cursor },
  orderBy: { id: "asc" }
});
```

## Best Practices

### Schema Design Practices

- Use `cuid()` or `uuid()` as default IDs instead of `autoincrement()` for distributed systems
- Add `@@map()` to use plural table names while keeping models singular
- Define explicit many-to-many relations when you need additional fields on the join table
- Use enums for fields with a fixed set of values
- Add indexes for fields used in `where`, `orderBy`, and `@@unique` constraints
- Use `@updatedAt` on models that track modification time
- Set `relationMode = "prisma"` for MongoDB support

### Code Organization

- Create a single Prisma Client instance (singleton pattern) to avoid connection exhaustion
- Place Prisma Client in a dedicated `lib/prisma.ts` or `lib/db.ts` file
- Use separate schema files with `@@schema("schemaName")` for multi-schema databases
- Keep migration files in version control for reproducibility
- Use `.env` files for connection strings; never commit secrets

### Performance Practices

- Use `select` instead of `include` to fetch only needed fields
- Use `lean` queries equivalent by selecting only required fields
- Implement pagination with cursor-based pagination for large datasets
- Use batch operations (`createMany`, `updateMany`, `deleteMany`) for bulk operations
- Avoid N+1 queries by using `include` or nested `select` for relations
- Use raw queries for complex SQL that Prisma cannot express
- Consider using `Prisma Accelerate` for connection pooling and caching
- Use `@@index` for composite indexes on frequently queried fields

### Security Practices

- Never log or expose Prisma Client query parameters containing sensitive data
- Use `$queryRaw` over `$queryRawUnsafe` to prevent SQL injection
- Validate user input before passing to Prisma queries
- Use connection pooling with `connection_limit` in production
- Configure `DATABASE_URL` with limited permissions (read/write on specific tables)
- Audit Prisma Client version for security advisories

## Common Mistakes

- **Creating Prisma Client repeatedly in serverless**: In serverless functions, create a singleton using global object to avoid exhausting database connections.
- **Using `include` without `select`**: Including entire related documents returns all fields. Use `select` to fetch only needed columns.
- **Missing indexes on foreign keys**: Prisma does not auto-index foreign keys. Add `@@index` for relation fields used in queries.
- **N+1 queries from lazy loading**: Without `include`, accessing a relation property triggers an additional query. Use `include` or `select` with relations.
- **Large `skip` for pagination**: Skipping many rows is slow. Use cursor-based pagination with `cursor` and `take`.
- **Mutating Prisma result objects**: Prisma results are read-only. Clone or spread the result before modification.
- **Not handling connection pool exhaustion**: Slow queries can exhaust the connection pool. Set appropriate timeouts and connection limits.
- **Using `create` instead of `createMany` for bulk inserts**: `create` in a loop sends individual queries. Use `createMany` for batch operations.
- **Forgetting `@updatedAt` for timestamp tracking**: Without `@updatedAt`, you must manually update timestamp fields.
- **Committing migration files directly to main without review**: Migration SQL should be reviewed for correctness, especially production environments.

## Libraries

### Prisma Ecosystem

| Library | Purpose |
|---------|---------|
| @prisma/client | Auto-generated type-safe query client |
| prisma | CLI for migrations, studio, and schema management |
| @prisma/nextjs-monorepo-workaround-plugin | Next.js monorepo support |
| prisma-extension-pagination | Cursor-based pagination helpers |
| prisma-nestjs-graphql | Generate NestJS/GraphQL types from Prisma schema |
| typegraphql-prisma | TypeGraphQL integration with Prisma |
| prisma-relay-cursor-connection | Relay cursor connection support |
| prisma-json-types-generator | Type-safe JSON field types |
| prisma-dbml-generator | Generate DBML diagrams from schema |

### Complementary Tools

| Tool | Purpose |
|------|---------|
| Prisma Studio | Web-based database GUI for CRUD operations |
| Prisma Data Platform | Database management, migration, and monitoring |
| Prisma Accelerate | Global connection pooling and caching |
| Prisma Pulse | Real-time database change streaming |
| PgBouncer | Connection pooling for PostgreSQL |
| PlanetScale | MySQL-compatible serverless database (works with Prisma) |

## Design Principles

### Single Source of Truth

The Prisma schema file should be the authoritative definition of your database schema. All team members should derive their understanding of the data model from the schema file.

### Type Safety as a Priority

Leverage Prisma's generated types extensively. Use `Prisma.UserSelect`, `Prisma.UserInclude`, and model types to ensure compile-time type safety for all database operations. This eliminates an entire class of runtime errors.

### Migration-First Schema Evolution

Always evolve your schema through migrations, never through ad-hoc database changes. Review generated SQL before applying. Use `prisma migrate dev` for development and `prisma migrate deploy` for production.

### Separation of Concerns

Keep business logic out of Prisma schema definitions. The schema should express data relationships and constraints only. Business rules should be implemented in application services that use Prisma Client.

## Coding Standards

### Schema File Organization

```prisma
// 1. Datasource and generator (top)
datasource db { ... }
generator client { ... }

// 2. Enums
enum Role { ... }

// 3. Models in alphabetical or logical order
model User { ... }
model Post { ... }

// 4. Model attributes at bottom
// @@map, @@index on their own lines
```

### Field Ordering Convention

```prisma
model User {
  // 1. Primary key
  id        String   @id @default(cuid())
  // 2. Scalar fields
  email     String   @unique
  name      String?
  password  String
  role      Role     @default(USER)
  // 3. Relation fields
  posts     Post[]
  profile   Profile?
  // 4. Timestamps
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Query Naming

- Use descriptive variable names: `activeUsers`, `publishedPosts`
- Use singular/plural consistently with the model name
- Prefix batch operations with `batch`: `batchCreateUsers`
- Use action verbs: `getUserById`, `updateUserProfile`, `deleteInactivePosts`

### Error Handling

```typescript
import { Prisma } from '@prisma/client'

try {
  await prisma.user.create({ data: { email: "existing@example.com" } })
} catch (error) {
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === 'P2002') {
      // Unique constraint violation
    }
    if (error.code === 'P2025') {
      // Record not found
    }
  }
  if (error instanceof Prisma.PrismaClientValidationError) {
    // Invalid data provided
  }
}
```

### Environment-Specific Configuration

```prisma
// schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// .env (local)
DATABASE_URL="postgresql://localhost:5432/mydb"

// .env.production (deployed)
DATABASE_URL="postgresql://user:pass@prod-host:5432/proddb?connection_limit=10&pool_timeout=10"
```
