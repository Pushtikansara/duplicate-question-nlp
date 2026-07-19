---
name: express
description: Use when building web APIs and server applications with Express.js. Covers routing, middleware, error handling, and security.
---

# Express.js Skill

## Overview
Express.js is a minimal and flexible Node.js web application framework that provides a robust set of features for web and mobile applications. It provides a thin layer of fundamental web application features without obscuring Node.js features.

## Instructions
- Use `express.Router()` for modular route handling instead of mounting routes directly on the app
- Always implement centralized error handling middleware as the last middleware
- Use `express.json()` and `express.urlencoded()` body parsers for JSON and form data
- Keep route handlers thin — extract business logic into service modules
- Validate request data at the middleware layer using Zod or Joi
- Use environment variables for configuration; validate them at startup
- Enable `trust proxy` when running behind a reverse proxy (Nginx, Cloudflare, AWS ELB)
- Use `compression` middleware for gzip/brotli response compression
- Implement rate limiting with `express-rate-limit` for all API routes
- Add security headers with `helmet` middleware
- Use `cors` middleware for cross-origin requests; configure origins explicitly
- Structure middleware order: security, parsing, logging, authentication, validation, routes, error handling
- Use `asyncHandler` wrapper for async route handlers to avoid uncaught promise rejections

## Core Concepts

### Middleware
- Middleware functions have access to `req`, `res`, and `next`
- Execute in the order they are registered
- Can modify `req` and `res` objects, end the request, or call `next()`
- Application-level: `app.use(middleware)` — runs on every request
- Router-level: `router.use(middleware)` — runs on routes within that router
- Error-handling middleware: four arguments `(err, req, res, next)` — runs when `next(err)` is called
- Built-in middleware: `express.json()`, `express.urlencoded()`, `express.static()`
- Third-party middleware: `helmet`, `cors`, `compression`, `morgan`

### Routing
- `app.get()`, `app.post()`, `app.put()`, `app.patch()`, `app.delete()`
- Route parameters: `:paramName` — accessed via `req.params`
- Query parameters: accessed via `req.query`
- Route chaining: `router.route('/users').get(...).post(...).put(...)`
- Multiple callbacks: `app.get('/route', middleware1, middleware2, handler)`
- Regular expression routes (avoid when possible — use string patterns)

### Request Object (req)
- `req.params` — route parameters
- `req.query` — URL query string parameters
- `req.body` — parsed request body (requires body-parser middleware)
- `req.headers` — HTTP headers (lowercase keys)
- `req.cookies` — cookies (requires `cookie-parser` middleware)
- `req.ip` — client IP address
- `req.path` — request path
- `req.method` — HTTP method
- `req.get(field)` — get a specific header

### Response Object (res)
- `res.json(body)` — send JSON response
- `res.status(code)` — set HTTP status code
- `res.send(body)` — send response of various types
- `res.redirect(url)` — redirect to a URL
- `res.render(view, data)` — render a template
- `res.sendFile(path)` — send a file
- `res.set(field, value)` — set response headers
- `res.cookie(name, value, options)` — set cookies
- `res.type(type)` — set Content-Type

## Examples

### Application Setup with Middleware
```javascript
import express from 'express'
import helmet from 'helmet'
import cors from 'cors'
import compression from 'compression'
import morgan from 'morgan'
import { rateLimit } from 'express-rate-limit'
import { errorHandler } from './middleware/errorHandler.js'
import { router } from './routes/index.js'

const app = express()

// Security headers
app.use(helmet())

// CORS
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') ?? '*',
  credentials: true,
}))

// Compression
app.use(compression())

// Request logging
app.use(morgan('combined'))

// Rate limiting
app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
}))

// Body parsing
app.use(express.json({ limit: '1mb' }))
app.use(express.urlencoded({ extended: true, limit: '1mb' }))

// Routes
app.use('/api/v1', router)

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// Centralized error handler (must be last)
app.use(errorHandler)

export { app }
```

### Router with Validation
```javascript
import { Router } from 'express'
import { z } from 'zod'
import { validate } from '../middleware/validate.js'
import * as userController from '../controllers/userController.js'
import { authenticate } from '../middleware/auth.js'

const router = Router()

// Validation schemas
const createUserSchema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
  password: z.string().min(8).max(128),
  role: z.enum(['user', 'admin']).default('user'),
})

const updateUserSchema = z.object({
  name: z.string().min(2).max(100).optional(),
  email: z.string().email().optional(),
})

// Routes
router.get('/users', authenticate, userController.list)
router.get('/users/:id', authenticate, userController.getById)
router.post('/users', validate(createUserSchema), userController.create)
router.put('/users/:id', authenticate, validate(updateUserSchema), userController.update)
router.delete('/users/:id', authenticate, userController.remove)

export { router }
```

### Async Handler Wrapper
```javascript
export function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next)
  }
}

// Usage in controller
import { asyncHandler } from '../middleware/asyncHandler.js'

export const getById = asyncHandler(async (req, res) => {
  const { id } = req.params
  const user = await db.users.findUnique({ where: { id } })

  if (!user) {
    return res.status(404).json({ error: 'User not found' })
  }

  res.json({ data: user })
})
```

### Error Handler Middleware
```javascript
export class AppError extends Error {
  constructor(statusCode, message) {
    super(message)
    this.statusCode = statusCode
    this.isOperational = true
    Error.captureStackTrace(this, this.constructor)
  }
}

export function errorHandler(err, req, res, next) {
  // Log error
  console.error({
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
  })

  // Operational error (expected)
  if (err.isOperational) {
    return res.status(err.statusCode).json({
      error: err.message,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
    })
  }

  // Programming or unknown error — don't leak details
  res.status(500).json({
    error: 'Internal server error',
  })
}
```

### Rate Limiter with Custom Handler
```javascript
import { rateLimit } from 'express-rate-limit'

export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  message: { error: 'Too many login attempts, please try again later' },
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res, next, options) => {
    res.status(options.statusCode).json({
      error: options.message,
      retryAfter: Math.ceil(options.windowMs / 1000),
    })
  },
})
```

## Best Practices
- Structure routes as thin controllers that delegate to service layer
- Use dependency injection for services to enable testing
- Version your API with URL prefixes (`/api/v1/`)
- Use HTTP status codes consistently (201 for created, 204 for no content, etc.)
- Implement pagination with query parameters (`page`, `limit`, `cursor`)
- Return consistent response shapes: `{ data, meta, error }` envelope
- Use CORS whitelist instead of `origin: '*'` for sensitive APIs
- Validate Content-Type headers for POST/PUT endpoints
- Set reasonable body size limits to prevent DoS attacks
- Use `compression` only for text responses (not binary data)
- Implement request ID for tracing: `req.id = crypto.randomUUID()`
- Use structured logging with correlation IDs for debugging

## Common Mistakes
- Not handling async errors — unhandled promise rejections crash the process
- Putting all routes in a single file instead of using Router
- Not using proper HTTP status codes (sending 200 for errors)
- Exposing stack traces to clients in production
- Using `app.use()` after route handlers and expecting middleware to run
- Not calling `next()` in middleware (hangs the request)
- Mutating `req` or `res` objects without considering middleware order
- Using `express.static` without a CDN for production assets
- Not validating user input (leading to injection attacks)
- Using synchronous operations in request handlers (blocks the event loop)
- Not implementing request timeouts (requests can hang indefinitely)
- Storing sessions in memory instead of Redis for production deployment

## Libraries
- **helmet** — secure HTTP headers
- **cors** — cross-origin resource sharing
- **compression** — gzip/brotli response compression
- **morgan** — HTTP request logging
- **express-rate-limit** — rate limiting
- **express-validator** — request validation middleware
- **cookie-parser** — cookie parsing
- **express-session** — session middleware
- **passport** — authentication middleware
- **swagger-jsdoc** + **swagger-ui-express** — OpenAPI documentation
- **multer** — multipart/form-data (file uploads)
- **express-async-errors** — automatic async error handling (alternative to wrapper)

## Design Principles
- **Middleware Pipeline**: Requests pass through a chain of middleware functions
- **Separation of Concerns**: Routes handle routing, controllers handle request/response, services handle business logic
- **Convention over Configuration**: Standard patterns for error handling, validation, and routing
- **Thin Controllers, Fat Services**: Keep route handlers minimal; put logic in services
- **Error Propagation**: Throw errors in services, catch and format in error middleware
- **Request-Response Cycle**: Each request creates a scope; use `res.locals` for request-scoped data

## Coding Standards
- Use ESM (`import`/`export`) for all new projects
- File naming: kebab-case for modules, PascalCase for classes
- Group by feature: `users/userRoutes.js`, `users/userController.js`, `users/userService.js`, `users/userValidation.js`
- Route file exports a `Router` instance
- Controller methods follow naming convention: `list`, `getById`, `create`, `update`, `remove`
- Service methods follow same naming but in service files
- Validation schemas defined separately and imported in routes
- Error classes extend `AppError` base class
- Environment variables validated at app startup with Zod
- Use `req.get('X-Request-Id')` or `crypto.randomUUID()` for trace IDs

## Testing
- Use **supertest** for HTTP integration tests with the Express app
- Mock database operations or use testcontainers for real DB testing
- Test middleware in isolation with `req`/`res` mocks
- Test error handling paths by triggering errors in services
- Use `nock` or `msw` for mocking external HTTP calls
- Use `node:test` or vitest for unit tests
- Test validation middleware with valid and invalid inputs
- Test rate limiting by checking `Retry-After` headers
- Test CORS by checking `Access-Control-Allow-Origin` headers
- Test session/cookie behavior with `supertest` session support
