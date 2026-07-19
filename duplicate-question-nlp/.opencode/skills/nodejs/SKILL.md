---
name: nodejs
description: Use when building server-side applications with Node.js. Covers event loop, streams, async patterns, module system, and production practices.
---

# Node.js Skill

## Overview
Node.js is a JavaScript runtime built on Chrome's V8 engine that enables server-side execution of JavaScript. It uses an event-driven, non-blocking I/O model that makes it lightweight and efficient for data-intensive real-time applications running across distributed devices.

## Instructions
- Use the built-in `node:` protocol for importing Node.js core modules (e.g., `import { readFile } from 'node:fs/promises'`)
- Prefer ESM (`import`/`export`) over CommonJS (`require`) for new projects
- Use `node --watch` for development with auto-restart (Node 18+)
- Handle all promise rejections — unhandled rejections crash the process in future Node versions
- Use environment variables with `process.env` for configuration; validate with Zod or env-schema
- Always use the `fs/promises` API instead of callback-based `fs`
- Use `AbortController`/`AbortSignal` for canceling async operations
- Use `process.on('unhandledRejection')` and `process.on('uncaughtException')` for global error handling
- Run with `--enable-source-maps` for proper stack traces in production
- Use `cluster` or PM2 for multi-core utilization in production

## Core Concepts

### Event Loop
- Node.js is single-threaded but uses an event loop for asynchronous I/O
- Event loop phases: timers, pending callbacks, idle/prepare, poll, check, close callbacks
- `setTimeout` and `setInterval` run in the timers phase
- `setImmediate` runs in the check phase (after I/O callbacks)
- `process.nextTick` runs before the next event loop tick (highest priority)
- Long-running synchronous operations block the event loop — use workers or split into chunks
- The event loop exits when there are no more active handles (timers, sockets, etc.)

### Module System
- ESM: `import`/`export` — static, top-level await, tree-shakable
- CommonJS: `require()`/`module.exports` — dynamic, synchronous
- Dual package support: package.json `exports` field for hybrid CJS/ESM
- Use `import.meta.url` for `__dirname` equivalent in ESM
- NPM packages should have proper `exports` map for package entry points
- Internal modules: prefix with `_` for private modules (convention only)
- Use `--experimental-detect-module` for auto-detecting module type

### Buffers and Streams
- `Buffer` for binary data handling (not `Uint8Array` directly)
- Streams: Readable, Writable, Duplex, Transform
- `pipeline()` for piping streams with error handling (preferred over `.pipe()`)

### Child Processes
- `child_process.spawn()` for long-running processes with streaming I/O
- `child_process.exec()` for short commands needing a shell
- `child_process.fork()` for spawning Node.js processes with IPC
- `worker_threads` for CPU-intensive tasks without blocking the event loop

## Examples

### Production HTTP Server
```javascript
import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
import { join, extname } from 'node:path'

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`)
    let filePath = join('public', url.pathname === '/' ? 'index.html' : url.pathname)
    const ext = extname(filePath)

    // Security: prevent directory traversal
    if (!filePath.startsWith(join(process.cwd(), 'public'))) {
      res.writeHead(403)
      return res.end('Forbidden')
    }

    const content = await readFile(filePath)
    res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] ?? 'application/octet-stream' })
    res.end(content)
  } catch (err) {
    if (err.code === 'ENOENT') {
      res.writeHead(404)
      res.end('Not Found')
    } else {
      console.error('Server error:', err)
      res.writeHead(500)
      res.end('Internal Server Error')
    }
  }
})

server.listen(3000, () => console.log('Server running on port 3000'))
```

### Stream Processing
```javascript
import { createReadStream, createWriteStream } from 'node:fs'
import { createGzip } from 'node:zlib'
import { pipeline } from 'node:stream/promises'
import { Transform } from 'node:stream'

// Transform stream for logging
const logTransform = new Transform({
  transform(chunk, encoding, callback) {
    console.log(`Processing ${chunk.length} bytes`)
    callback(null, chunk)
  },
})

// Compress a file with logging
async function compressFile(input, output) {
  try {
    await pipeline(
      createReadStream(input),
      logTransform,
      createGzip(),
      createWriteStream(output),
    )
    console.log('Compression complete')
  } catch (err) {
    console.error('Pipeline failed:', err)
  }
}
```

### Worker Threads for CPU-bound Tasks
```javascript
// main.js
import { Worker } from 'node:worker_threads'
import { cpus } from 'node:os'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))

function runInWorker(data) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(join(__dirname, 'worker.js'), {
      workerData: data,
    })
    worker.on('message', resolve)
    worker.on('error', reject)
    worker.on('exit', code => {
      if (code !== 0) reject(new Error(`Worker stopped with exit code ${code}`))
    })
  })
}

const numWorkers = cpus().length
const tasks = Array.from({ length: 100 }, (_, i) => i)
const results = await Promise.all(tasks.map(task => runInWorker(task)))
```

```javascript
// worker.js
import { workerData, parentPort } from 'node:worker_threads'

function heavyComputation(input) {
  let result = 0
  for (let i = 0; i < 1000000; i++) {
    result += Math.sqrt(input * i)
  }
  return result
}

parentPort.postMessage(heavyComputation(workerData))
```

### Graceful Shutdown
```javascript
import { createServer } from 'node:http'
import { setTimeout } from 'node:timers/promises'

const server = createServer((req, res) => {
  setTimeout(5000).then(() => {
    res.writeHead(200)
    res.end('Hello')
  })
})

server.listen(3000)

const shutdown = async (signal) => {
  console.log(`Received ${signal}, shutting down gracefully...`)

  server.close(() => {
    console.log('HTTP server closed')
  })

  await setTimeout(10000)
  console.error('Forced shutdown after timeout')
  process.exit(1)
}

process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)
```

## Best Practices
- Always use `try/catch` with `await` or `.catch()` with promises
- Use `pino` or `winston` for structured logging (avoid `console.log` in production)
- Validate environment variables at startup with Zod schema
- Implement graceful shutdown: close servers, drain connections, flush logs
- Use `node --heapsnapshot-signal` for capturing heap snapshots on-demand
- Set `UV_THREADPOOL_SIZE` based on CPU count for I/O intensive tasks
- Use `NODE_ENV=production` for production (disables development warnings)
- Enable `trust proxy` when running behind a reverse proxy
- Use `compression` middleware for gzip/brotli response compression
- Use `helmet` for security headers in HTTP servers
- Set memory limits with `--max-old-space-size` flag
- Use health check endpoints (`/health`, `/ready`) for orchestration

## Common Mistakes
- Not handling promise rejections (results in unhandledRejection warning/crash)
- Using synchronous `fs` methods (`readFileSync`) in request handlers (blocks the event loop)
- Not implementing backpressure with streams (can crash the process with memory overflow)
- Using `process.exit()` without graceful shutdown (drops active connections)
- Assuming `JSON.parse` never throws in request handlers
- Not using `AbortController` for HTTP requests that might hang
- Storing secrets in code instead of environment variables
- Using `require()` in ESM files or `import` in CommonJS without proper setup
- Not handling the `error` event on streams and EventEmitters
- Creating too many child processes without managing concurrency
- Using `cluster` without sticky sessions when using multiple processes

## Libraries
- **express** / **fastify** — HTTP framework
- **pino** — structured logging (fastest JSON logger)
- **zod** — schema validation with TypeScript inference
- **dotenv** — load .env files
- **pg** / **@prisma/client** — PostgreSQL client/ORM
- **ioredis** — Redis client (supports cluster and sentinel)
- **bullmq** — job queue with Redis
- **socket.io** — WebSocket with fallback transports
- **helmet** — security headers middleware
- **compression** — HTTP compression middleware
- **pm2** — production process manager with auto-restart
- **dotenv-expand** — variable expansion in .env files
- **agentkeepalive** — HTTP keep-alive agent for better connection pooling
- **rate-limiter-flexible** — rate limiting with various backends

## Design Principles
- **Non-blocking I/O**: Every I/O operation uses callbacks, promises, or async/await
- **Event-Driven**: Applications react to events (HTTP requests, file changes, socket data)
- **Single-Threaded + Workers**: Main thread handles I/O; CPU work goes to worker threads
- **Minimal Core**: Node.js core is small; functionality comes from npm packages
- **Convention over Configuration**: Standard project structure patterns for clarity
- **Reusable Modules**: Small, focused, composable packages via npm

## Coding Standards
- Use ESM (`import`/`export`) for all new projects
- File extension: `.js` for CommonJS, `.mjs` for ESM, `.cjs` for explicit CommonJS in ESM projects
- Use `node:` prefix for built-in modules
- Use `const` and `let` only; never `var`
- Async functions for any I/O operations
- One default export per module for the main function/class
- Named exports for utilities and helpers
- Use `Error` subclassing for custom error types
- Add `"type": "module"` in package.json for ESM
- Define `engines` field in package.json to specify Node version

## Security
- Validate and sanitize all user input
- Use parameterized queries for SQL/NoSQL databases
- Set `httpOnly` and `secure` flags on cookies
- Implement CSRF protection for state-changing operations
- Use rate limiting to prevent brute-force attacks
- Set reasonable request size limits (body-parser limit)
- Use `helmet` for security headers (CSP, X-Frame-Options, HSTS)
- Validate JSON schemas for API request bodies
- Sanitize file uploads — check file type, size, and scan for malware
- Use HTTP/2 or HTTP/3 for transport security
- Keep dependencies updated with `npm audit` and Dependabot

## Testing
- Use **vitest** or **node:test** (built-in test runner since Node 18)
- Write tests in `test/` directory mirroring source structure
- Use `supertest` for HTTP integration tests
- Mock external services with `nock` or `msw`
- Use `testcontainers` for integration tests with real databases
- Set `NODE_ENV=test` and `NODE_OPTIONS=--experimental-vm-modules` for testing
- Use coverage thresholds with `--experimental-test-coverage`
- Test error paths and edge cases, not just happy paths
- Use `sinon` for stubs, spies, and mocks
- Write E2E tests with Playwright for HTTP APIs
