---
name: graphql
description: Use when designing or implementing GraphQL APIs. Covers schema design, resolvers, queries, mutations, subscriptions, and federation.
---

# GraphQL Skill

## Overview
GraphQL is a query language for APIs and a runtime for executing those queries with your existing data. It provides a complete and understandable description of the data in your API, gives clients the power to ask for exactly what they need, and makes it easier to evolve APIs over time.

## Instructions
- Design the schema first — it's the contract between client and server
- Use the Schema Definition Language (SDL) for defining types before writing resolvers
- Follow the principle of "only request what you need" on the client side
- Use DataLoader for batching and caching database queries to solve N+1 problems
- Implement proper authentication and authorization at the resolver level
- Use `@deprecated` directive for fields that should be phased out
- Limit query depth and complexity to prevent malicious queries
- Use pagination with the Relay connection spec for list fields
- Avoid multiple mutations in a single request unless they are semantically grouped
- Use enums for fields with a fixed set of values
- Make nullable fields the default; only use non-null (`!`) when the field is truly guaranteed
- Use custom scalars for domain-specific types (Date, URL, JSON, etc.)

## Core Concepts

### Schema Design
- `type Query` — entry point for read operations
- `type Mutation` — entry point for write operations
- `type Subscription` — entry point for real-time events
- Object types: `type User { id: ID! name: String! email: String }`
- Input types: `input CreateUserInput { name: String! email: String! }`
- Enums: `enum Role { ADMIN USER VIEWER }`
- Interfaces: `interface Node { id: ID! }` — shared fields across types
- Unions: `union SearchResult = User | Post | Comment` — one of multiple types
- Custom scalars: `scalar DateTime` — domain-specific values
- Directives: `@deprecated`, `@skip`, `@include`, custom directives for auth, formatting

### Resolvers
- Every field in the schema maps to a resolver function
- Resolvers receive: `(parent, args, context, info)`
- `parent` — return value of the parent resolver (for nested fields)
- `args` — arguments passed to the field
- `context` — shared context (auth user, DB connection, DataLoader instances)
- `info` — query metadata (selection set, field name, path)
- Default resolver: if no resolver is defined, GraphQL looks for a property with the same name on the parent object

### Mutations
- Mutations are executed sequentially (unlike queries which run in parallel)
- Always return the mutated object so clients can update their cache
- Use input types for mutation arguments
- Return a `Payload` type for mutations: `{ user: User!, errors: [Error!] }`
- Include `clientMutationId` for idempotency if needed

### Subscriptions
- Real-time communication over WebSockets
- Use `subscribe` function to return an AsyncIterator
- Common use cases: notifications, live updates, chat messages
- Server sends events when data changes; client subscribes to specific events
- Authentication happens at connection time and can be revalidated per event
- Use `graphql-ws` or `subscriptions-transport-ws` for transport

### Federation
- Distributed GraphQL architecture where multiple services compose into a single graph
- Each service defines its own schema with `@key` directives
- Gateway stitches schemas together and routes requests to the right service
- Service A: `type User @key(fields: "id") { id: ID! name: String! }`
- Service B: `type User @key(fields: "id") { id: ID! reviews: [Review!] }`
- `@external`, `@requires`, `@provides` directives for cross-service field dependencies
- Apollo Federation and Netflix Domain Graph Service (DGS) are common implementations

## Examples

### Schema Definition
```graphql
type Query {
  user(id: ID!): User
  users(page: Int, limit: Int): UserConnection!
  posts(filters: PostFilters): [Post!]!
  search(query: String!): [SearchResult!]!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
  addComment(postId: ID!, content: String!): Comment!
}

type Subscription {
  commentAdded(postId: ID!): Comment!
  userOnline: User!
}

type User {
  id: ID!
  name: String!
  email: String
  avatar: String
  posts: [Post!]!
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
  createdAt: DateTime!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
  createdAt: DateTime!
}

union SearchResult = User | Post

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type CreateUserPayload {
  user: User
  errors: [Error!]
}

type Error {
  field: String
  message: String!
}

input CreateUserInput {
  name: String!
  email: String!
  password: String!
}

input PostFilters {
  authorId: ID
  search: String
  createdAtAfter: DateTime
}

scalar DateTime
```

### Resolver Implementation (Apollo Server)
```typescript
import { ApolloServer } from '@apollo/server'
import { startStandaloneServer } from '@apollo/server/standalone'
import DataLoader from 'dataloader'

interface Context {
  user: User | null
  loaders: {
    userLoader: DataLoader<string, User>
    commentLoader: DataLoader<string, Comment[]>
  }
}

const resolvers = {
  Query: {
    user: async (_, { id }, { loaders }) => {
      return loaders.userLoader.load(id)
    },
    users: async (_, { page = 1, limit = 10 }, { loaders }) => {
      const users = await db.users.findAll({ skip: (page - 1) * limit, take: limit })
      return connectionFromArray(users, { page, limit })
    },
    search: async (_, { query }, context) => {
      const [users, posts] = await Promise.all([
        db.users.search(query),
        db.posts.search(query),
      ])
      return [...users, ...posts]
    },
  },
  Mutation: {
    createUser: async (_, { input }, { user }) => {
      if (!user?.isAdmin) {
        return { user: null, errors: [{ field: null, message: 'Unauthorized' }] }
      }
      const newUser = await db.users.create(input)
      return { user: newUser, errors: [] }
    },
    addComment: async (_, { postId, content }, { user }) => {
      if (!user) throw new AuthenticationError('Not authenticated')
      return db.comments.create({ postId, content, authorId: user.id })
    },
  },
  Subscription: {
    commentAdded: {
      subscribe: (_, { postId }, { pubsub }) => {
        return pubsub.asyncIterator(`COMMENT_ADDED:${postId}`)
      },
    },
  },
  User: {
    posts: async (parent, _, { loaders }) => {
      return loaders.postLoader.load(parent.id)
    },
  },
  SearchResult: {
    __resolveType: (obj) => {
      if (obj.title) return 'Post'
      if (obj.name) return 'User'
      return null
    },
  },
}
```

### DataLoader for Batching
```typescript
import DataLoader from 'dataloader'

async function batchUsers(ids: readonly string[]) {
  const users = await db.users.findByIds(ids as string[])
  const userMap = new Map(users.map(u => [u.id, u]))
  return ids.map(id => userMap.get(id) || null)
}

async function batchComments(postIds: readonly string[]) {
  const comments = await db.comments.findByPostIds(postIds as string[])
  const grouped = new Map<string, Comment[]>()
  for (const comment of comments) {
    if (!grouped.has(comment.postId)) grouped.set(comment.postId, [])
    grouped.get(comment.postId)!.push(comment)
  }
  return postIds.map(id => grouped.get(id) || [])
}

// In context creation
const context: Context = {
  user: authenticatedUser,
  loaders: {
    userLoader: new DataLoader(batchUsers),
    commentLoader: new DataLoader(batchComments),
  },
}
```

### Apollo Federation Schema
```graphql
# Subgraph A: User Service
extend type Query {
  user(id: ID!): User
}

type User @key(fields: "id") {
  id: ID!
  name: String!
  email: String!
}

# Subgraph B: Review Service
type Review @key(fields: "id") {
  id: ID!
  rating: Int!
  content: String!
  author: User! @provides(fields: "name")
}

extend type User @key(fields: "id") {
  id: ID! @external
  name: String! @external
  reviews: [Review!]
}
```

## Best Practices
- Keep mutations atomic — one mutation should do one thing
- Use `null` for missing/optional data; avoid `null` for errors
- Implement cursor-based pagination (Relay spec) over offset-based for consistency
- Use `@deprecated` with a reason string when removing fields
- Version your schema via field deprecation, not API version numbers
- Write integration tests for GraphQL queries and mutations
- Use persisted queries in production to reduce request size and improve security
- Implement query complexity analysis to prevent expensive queries
- Use field-level authorization with custom directives or middleware
- Cache query results with response caching (ApServer or GraphCDN)
- Validate input arguments at the schema level with custom scalars

## Common Mistakes
- Exposing database schema directly as GraphQL types (tight coupling)
- Making all fields required (`!`) leading to breaking changes on every schema evolution
- Not using DataLoader — causes N+1 queries for list fields
- Putting business logic in resolvers instead of service layers
- Over-fetching through deeply nested queries without complexity limits
- Not implementing proper error handling in resolvers
- Using null for errors instead of a proper error type in the schema
- Making mutations that don't return the affected object (clients can't update cache)
- Not handling subscription authentication properly
- Using offset-based pagination which has performance issues with large datasets
- Creating overly broad mutations that accept many optional fields
- Forgetting that resolvers can run in parallel for query fields

## Libraries
- **@apollo/server** — Apollo Server for Node.js
- **@apollo/client** — Apollo Client for React/frontend
- **graphql-yoga** — Hive's GraphQL server (works with Deno, Bun, Node)
- **type-graphql** — TypeScript-first schema creation with decorators
- **pothos** — TypeScript schema builder (code-first, strongly typed)
- **graphql-code-generator** — generate TypeScript types from GraphQL schema
- **graphql-playground** — interactive GraphQL IDE (Altair is also popular)
- **dataloader** — batching and caching for database queries
- **apollo-federation** — Apollo Federation for distributed graph
- **graphql-query-complexity** — query complexity analysis
- **graphql-shield** — permission layer for GraphQL schemas
- **gqty** — frontend code generation and type-safe queries
- **relay** — Facebook's GraphQL client with advanced pagination and caching

## Design Principles
- **Schema-First**: Design the schema as the contract before implementing resolvers
- **Client-Driven**: Clients specify exactly what data they need in each request
- **Strongly Typed**: Every field has a defined type; validation happens at the API layer
- **Hierarchical**: Queries follow the shape of the data with nested selection sets
- **Single Endpoint**: One endpoint handles all queries, mutations, and subscriptions
- **Introspective**: The schema is self-documenting and queryable via `__schema`

## Coding Standards
- Types: PascalCase (`User`, `Post`, `UserConnection`)
- Fields: camelCase (`firstName`, `createdAt`)
- Enums: UPPER_CASE (`ADMIN`, `USER`) or PascalCase depending on convention
- Input types: suffix with `Input` (e.g., `CreateUserInput`)
- Payload types: suffix with `Payload` (e.g., `CreateUserPayload`)
- Connection types: `TypeConnection`, `TypeEdge` for pagination
- Arguments: camelCase, descriptive names
- Use singular for type names, plural for list field names
- Group schema files by domain: `user.graphql`, `post.graphql`, `comment.graphql`
- Keep schema files in a `schema/` directory

## Security
- Implement query depth limiting to prevent deeply nested malicious queries
- Use query complexity analysis to reject expensive queries
- Authenticate at the connection level for subscriptions
- Validate that clients can only access authorized data
- Implement rate limiting at the API layer
- Enable persisted queries to prevent arbitrary query execution
- Mask internal error details from clients (never expose stack traces)
- Use `@auth` directive or resolver-level checks for field authorization
- Limit batch request sizes to prevent resource exhaustion
- Validate input arguments with length limits and type checking
- Use CSRF tokens for mutations sent via cookies
- Implement WebSocket authentication for subscriptions
