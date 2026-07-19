---
name: rest-api
description: Use when designing or implementing RESTful APIs. Covers resource naming, HTTP methods, status codes, versioning, pagination, and HATEOAS.
---

# REST API Skill

## Overview
REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs use HTTP methods as verbs and resources as nouns, creating a stateless, cacheable, uniform interface between clients and servers.

## Instructions
- Model resources as nouns, not verbs: `/users`, `/orders`, `/products` not `/getUsers`, `/createOrder`
- Use HTTP methods correctly: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove)
- Use plural nouns for collection resources: `/users` not `/user`
- Use consistent URL patterns: `/resources`, `/resources/:id`, `/resources/:id/sub-resources`
- Return appropriate HTTP status codes for every response
- Version your API from the start; use URL prefix or header-based versioning
- Implement pagination for all list endpoints
- Use consistent error response formats across all endpoints
- Use HATEOAS (Hypermedia as the Engine of Application State) links in responses for discoverability
- Design for idempotency: GET, PUT, DELETE should be idempotent; POST is not
- Use query parameters for filtering, sorting, and field selection
- Use request body for complex POST/PUT/PATCH data, not query parameters
- Implement proper authentication and authorization for protected resources

## Core Concepts

### HTTP Methods
- **GET** — retrieve a resource or collection (safe, idempotent, cacheable)
- **POST** — create a new resource (non-idempotent, not cacheable by default)
- **PUT** — replace an entire resource (idempotent)
- **PATCH** — partially update a resource (not necessarily idempotent)
- **DELETE** — remove a resource (idempotent)
- **HEAD** — retrieve headers only (same as GET without body)
- **OPTIONS** — discover allowed methods for a resource

### HTTP Status Codes
- **200 OK** — successful GET, PUT, PATCH
- **201 Created** — successful POST (resource created)
- **202 Accepted** — request accepted but not yet processed (async operations)
- **204 No Content** — successful DELETE or PUT with no response body
- **301 Moved Permanently** — resource has been relocated
- **304 Not Modified** — cached version is still valid
- **400 Bad Request** — malformed request, validation errors
- **401 Unauthorized** — missing or invalid authentication
- **403 Forbidden** — authenticated but not authorized
- **404 Not Found** — resource does not exist
- **405 Method Not Allowed** — HTTP method not supported for this resource
- **409 Conflict** — resource state conflict (e.g., duplicate)
- **410 Gone** — resource intentionally removed
- **422 Unprocessable Entity** — semantic validation errors
- **429 Too Many Requests** — rate limiting
- **500 Internal Server Error** — unexpected server error
- **502 Bad Gateway** — upstream service failure
- **503 Service Unavailable** — server temporarily overloaded or down

### Resource Naming
- Use lowercase with hyphens: `/api/v1/blog-posts` not `/api/v1/blogPosts`
- Use plural nouns for collections: `/users`, `/orders`
- Use singular for singleton resources: `/profile`, `/settings`
- Nest related resources: `/users/:id/orders`
- Avoid deep nesting (max 2 levels deep): `/users/:id/orders/:orderId/items` is too deep
- Use query parameters for filtering, not path segments: `/orders?status=pending`
- Use `self` as the resource identifier in responses for HATEOAS

### Versioning
- URL prefix: `/api/v1/users`, `/api/v2/users` (most common)
- Header-based: `Accept: application/vnd.api+json; version=2`
- Query parameter: `/api/users?version=2` (least recommended — pollutes caching)
- Use major versions only (v1, v2); deprecate v1 when v2 is stable
- Don't version until you need to make a breaking change — keep backward compatibility

### Pagination
- Cursor-based pagination (recommended for large datasets): `?cursor=abc&limit=20`
- Offset-based pagination: `?page=2&limit=20`
- Include pagination metadata in responses:
  ```json
  {
    "data": [...],
    "meta": {
      "page": 2,
      "limit": 20,
      "total": 150,
      "totalPages": 8
    },
    "links": {
      "self": "/api/v1/users?page=2&limit=20",
      "first": "/api/v1/users?page=1&limit=20",
      "prev": "/api/v1/users?page=1&limit=20",
      "next": "/api/v1/users?page=3&limit=20",
      "last": "/api/v1/users?page=8&limit=20"
    }
  }
  ```

### HATEOAS
- Include links in responses to guide clients to related resources
- Standard link relations: `self`, `collection`, `next`, `prev`, `first`, `last`, `related`
- Links enable discoverability and reduce client-side URL construction
- Clients follow links instead of hardcoding URLs

### Filtering, Sorting, and Field Selection
- Filtering: `?status=active&category=electronics`
- Sorting: `?sort=name,-createdAt` (minus for descending)
- Field selection: `?fields=id,name,email` (sparse fieldsets)
- Complex filters: `?filter[name]=John&filter[age][gte]=18`

## Examples

### RESTful Endpoint Design
```
# User resources
GET    /api/v1/users              # List users (paginated)
POST   /api/v1/users              # Create user
GET    /api/v1/users/:id          # Get user by ID
PUT    /api/v1/users/:id          # Replace user (all fields)
PATCH  /api/v1/users/:id          # Partial update user
DELETE /api/v1/users/:id          # Delete user

# Nested resources
GET    /api/v1/users/:id/orders   # List user's orders
POST   /api/v1/users/:id/orders   # Create order for user

# Actions (use verbs only for non-CRUD operations)
POST   /api/v1/orders/:id/cancel  # Cancel an order
POST   /api/v1/orders/:id/ship    # Ship an order

# Search
GET    /api/v1/search?q=keyword&type=users
```

### Response Envelope
```json
// Success response
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "user",
    "attributes": {
      "name": "Alice Smith",
      "email": "alice@example.com",
      "role": "admin",
      "createdAt": "2025-01-15T10:30:00Z"
    },
    "relationships": {
      "orders": {
        "links": {
          "self": "/api/v1/users/550e8400/orders",
          "related": "/api/v1/users/550e8400/orders"
        }
      }
    },
    "links": {
      "self": "/api/v1/users/550e8400"
    }
  },
  "meta": {
    "requestId": "req-abc-123"
  }
}

// Collection response
{
  "data": [
    { "id": "...", "type": "user", "attributes": { ... } }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  },
  "links": {
    "self": "/api/v1/users?page=1&limit=20",
    "next": "/api/v1/users?page=2&limit=20",
    "last": "/api/v1/users?page=8&limit=20"
  }
}

// Error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address",
        "code": "INVALID_EMAIL"
      },
      {
        "field": "age",
        "message": "Must be at least 18",
        "code": "MIN_VALUE"
      }
    ],
    "requestId": "req-abc-123"
  }
}
```

### HATEOAS Example
```json
{
  "data": {
    "id": "123",
    "type": "order",
    "attributes": {
      "status": "pending",
      "total": 150.00,
      "items": 3
    },
    "links": {
      "self": "/api/v1/orders/123",
      "cancel": {
        "href": "/api/v1/orders/123/cancel",
        "method": "POST",
        "title": "Cancel this order"
      },
      "pay": {
        "href": "/api/v1/orders/123/payments",
        "method": "POST",
        "title": "Make a payment"
      },
      "user": {
        "href": "/api/v1/users/456",
        "title": "Order owner"
      }
    }
  }
}
```

## Best Practices
- Use consistent date/time format — ISO 8601 (`2025-01-15T10:30:00Z`) everywhere
- Use UUIDs for resource IDs (not auto-increment integers — they leak information)
- Implement ETags for conditional requests and caching
- Use `Cache-Control` headers for caching strategy
- Set `Content-Type: application/json` on all responses
- Accept `Content-Type: application/json` on all POST/PUT/PATCH requests
- Use gzip/brotli compression for responses
- Implement rate limiting with `X-RateLimit-*` headers
- Return `Location` header with the resource URL on POST (201 Created)
- Use `X-Request-Id` header for request tracing across services
- Implement idempotency keys for POST endpoints that need idempotent semantics
- Use OpenAPI/Swagger for API documentation

## Common Mistakes
- Using verbs in URLs (`/getUsers`, `/createUser`) instead of HTTP methods
- Returning 200 for all responses with error codes in the body
- Not returning proper status codes (using 200 for created, 200 for deleted)
- Exposing internal database IDs or implementation details
- Not validating input at the API boundary
- Using the same field names for different concepts across resources
- Not supporting pagination from the start (breaking change to add later)
- Deep nesting of resources (more than 2-3 levels)
- Not versioning the API from the beginning
- Returning 500 for validation errors (400/422 is more appropriate)
- Storing secrets or tokens in URLs (they get logged by proxies and servers)
- Using synchronous blocking operations for long-running requests

## Libraries
- **express** — Node.js REST API framework
- **fastapi** — Python REST API framework
- **drf** (Django REST Framework) — Python REST framework for Django
- **flask-restful** — REST API extension for Flask
- **openapi-generator** — generate clients from OpenAPI spec
- **swagger-ui** — interactive API documentation
- **redoc** — beautiful API documentation from OpenAPI
- **spectral** — OpenAPI linter and validator
- **connexion** — OpenAPI-first framework for Python
- **apimatic-validator** — API design validator
- **postman** / **bruno** — API client for testing and development
- **nock** — HTTP mocking for testing
- **zod** — request/response schema validation (with TypeScript)

## Design Principles
- **Statelessness**: Each request contains all necessary information; server does not store client state
- **Uniform Interface**: Consistent resource identification, representation manipulation, self-descriptive messages, HATEOAS
- **Resource-Oriented**: Everything is a resource identified by a URI
- **Representation**: Resources have multiple representations (JSON, XML); JSON is the standard
- **Cacheability**: Responses must be explicitly marked as cacheable or not
- **Layered System**: Client cannot tell if it's talking to the server, proxy, or gateway
- **Code on Demand (optional)**: Server can extend client functionality via downloadable code

## Coding Standards
- URL path: lowercase, hyphens, no trailing slash (except root)
- URL structure: `/api/{version}/{resource}[/{id}][/{sub-resource}]`
- JSON field names: camelCase (`firstName`, `createdAt`)
- Use `type` field in JSON:API or consistent `data`/`errors`/`meta` top-level keys
- Error codes: UPPER_SNAKE_CASE (`VALIDATION_ERROR`, `NOT_FOUND`)
- Request IDs: use UUIDs, passed as `X-Request-Id` header
- Responses always wrapped in envelope structure for consistency
- Links use relative paths from the API base URL
- Date fields: ISO 8601 in UTC (`2025-01-15T10:30:00Z`)
- Use consistent naming and types across all endpoints

## Security
- Always use HTTPS in production
- Implement authentication: JWT, OAuth 2.0, or API keys
- Validate Content-Type headers to prevent type confusion attacks
- Sanitize and validate all input to prevent injection attacks
- Use parameterized queries for database operations
- Set CORS headers explicitly — never use `Access-Control-Allow-Origin: *` with credentials
- Implement rate limiting per user/IP
- Use `Content-Security-Policy` headers for web-facing APIs
- Log security events (auth failures, rate limit violations, suspicious patterns)
- Rotate API keys and secrets regularly
- Mask sensitive fields (passwords, tokens) in logs and responses
- Implement request size limits to prevent DoS
- Use HTTP Strict Transport Security (HSTS) headers

## Performance
- Implement response caching with `Cache-Control` and ETags
- Use database indexing for commonly filtered/sorted fields
- Support sparse fieldsets to reduce response size
- Implement compression (gzip, brotli) on responses
- Use connection pooling for database connections
- Implement pagination with cursors for large datasets
- Use eager loading for related resources (avoid N+1 queries)
- Implement CDN caching for static/rarely-changed responses
- Use database read replicas for read-heavy workloads
- Asynchronous processing for long-running operations (202 Accepted + polling)
- Use HTTP/2 for multiplexed requests
- Monitor and optimize slow endpoints with APM tools
- Implement bulk endpoints for batch operations
- Use prepared statements for repeated database queries
