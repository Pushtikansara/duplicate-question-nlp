---
name: docker
description: Use when containerizing applications with Docker. Covers Dockerfiles, compose, networking, volumes, and best practices.
---

# Docker Skill

## Instructions

Docker is a platform for developing, shipping, and running applications in containers. Containers package software with all its dependencies, ensuring consistent behavior across environments. This skill covers writing Dockerfiles, using Docker Compose for multi-service applications, managing networking and volumes, and following best practices for containerized deployments.

### Dockerfile Fundamentals

A Dockerfile is a text document with instructions for building a Docker image. Each instruction creates a layer in the image.

```dockerfile
# Base image
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Define runtime command
CMD ["node", "dist/index.js"]
```

### Dockerfile Instructions Reference

| Instruction | Purpose |
|-------------|---------|
| FROM | Set base image for subsequent instructions |
| WORKDIR | Set working directory for RUN, CMD, ENTRYPOINT, COPY, ADD |
| COPY | Copy files from build context into the image |
| ADD | Like COPY but supports URLs and tar auto-extraction |
| RUN | Execute commands in a new layer |
| CMD | Provide defaults for executing container |
| ENTRYPOINT | Configure container to run as executable |
| EXPOSE | Document which ports the container listens on |
| ENV | Set environment variables |
| ARG | Build-time variables |
| LABEL | Add metadata to image |
| VOLUME | Create mount point for external volumes |
| USER | Set user for RUN, CMD, ENTRYPOINT |
| HEALTHCHECK | Command to check container health |
| SHELL | Override default shell |
| STOPSIGNAL | System call signal to stop container |

### Docker Compose

Docker Compose defines and runs multi-container applications using a YAML file:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: myapp
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### Networking

Docker provides several networking modes:

- **bridge**: Default network driver for standalone containers
- **host**: Container shares host network stack
- **overlay**: Multi-host networking for Swarm services
- **macvlan**: Assign MAC addresses to containers
- **none**: Disable networking

Use custom bridge networks for service discovery and isolation between containers.

### Volumes and Data Persistence

Docker provides three ways to persist data:

- **Bind mounts**: Mount host directory into container
- **Volumes**: Docker-managed storage in `/var/lib/docker/volumes/`
- **tmpfs mounts**: In-memory storage (non-persistent)

Prefer named volumes over bind mounts for production deployments. Use bind mounts for development with hot-reloading.

## Examples

### Example 1: Multi-stage Build for Node.js

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build
RUN npm prune --production

# Stage 2: Production
FROM node:20-alpine
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

### Example 2: Python Application with Poetry

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN adduser -D appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Example 3: Full Docker Compose with Multiple Services

```yaml
version: '3.8'

x-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
      POSTGRES_USER: ${POSTGRES_USER:-appuser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging: *default-logging
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redispass}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    logging: *default-logging
    restart: unless-stopped

  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "${APP_PORT:-3000}:3000"
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://appuser:${POSTGRES_PASSWORD:-secret}@postgres:5432/${POSTGRES_DB:-appdb}
      REDIS_URL: redis://:${REDIS_PASSWORD:-redispass}@redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    logging: *default-logging
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot_data:/var/www/certbot
    depends_on:
      - app
    logging: *default-logging
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  certbot_data:
```

### Example 4: Dockerfile Best Practices (Optimized for Cache)

```dockerfile
# 1. Use specific base image versions
FROM node:20.11.0-alpine3.19

# 2. Add metadata
LABEL maintainer="team@example.com"
LABEL version="1.0.0"
LABEL description="Production API service"

# 3. Install system dependencies early
RUN apk add --no-cache curl tini

# 4. Set up non-root user early
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# 5. Create app directory and set working directory
WORKDIR /app

# 6. Copy dependency files first (leverages cache)
COPY package*.json yarn.lock ./

# 7. Install dependencies
RUN yarn install --frozen-lockfile --production && \
    yarn cache clean

# 8. Copy application code
COPY --chown=appuser:appgroup . .

# 9. Build application
RUN yarn build

# 10. Switch to non-root user
USER appuser

# 11. Expose port
EXPOSE 3000

# 12. Use tini as init for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# 13. Command
CMD ["node", "dist/index.js"]
```

### Example 5: docker-compose for Development with Hot Reload

```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules  # Anonymous volume to avoid overwriting
    environment:
      - NODE_ENV=development
      - DEBUG=true
    command: npm run dev

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: app_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    volumes:
      - pg_dev_data:/var/lib/postgresql/data

volumes:
  pg_dev_data:
```

### Example 6: Docker Network Configuration

```yaml
version: '3.8'
services:
  app:
    build: .
    networks:
      - frontend
      - backend

  api:
    build: ./api
    networks:
      - backend
    ports:
      - "8080:8080"

  database:
    image: postgres:16
    networks:
      - backend
    # database is not exposed on frontend network

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### Example 7: Container Healthcheck Patterns

```yaml
# In Dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# In docker-compose
healthcheck:
  test: ["CMD", "pg_isready", "-U", "appuser"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

## Best Practices

### Dockerfile Best Practices

- Use specific base image versions (avoid `:latest`)
- Use multi-stage builds to minimize final image size
- Combine RUN commands with `&&` to reduce layer count
- Use `.dockerignore` to exclude unnecessary files from build context
- Sort multi-line arguments alphabetically
- Leverage build cache by ordering instructions from least to most frequently changing
- Use `COPY --chown` to set ownership at copy time
- Set `WORKDIR` instead of chaining `RUN mkdir` and `RUN cd`
- Use `EXPOSE` to document container ports
- Use `HEALTHCHECK` for production containers
- Run containers as non-root user for security
- Use `tini` or similar init system for proper signal handling
- Pin base image digests for immutable builds

### Docker Compose Best Practices

- Use named volumes for persistent data
- Set resource limits (CPU, memory) for each service
- Configure logging driver with rotation
- Use health checks for service dependencies
- Use environment variables with `.env` files
- Define restart policies for production services
- Separate development and production compose files
- Use `depends_on` with health checks for proper startup ordering
- Use extensions (`x-`) for shared configuration

### Security Best Practices

- Never store secrets in Dockerfiles or images
- Use Docker secrets or environment variables for sensitive data
- Run containers with read-only root filesystem where possible
- Drop Linux capabilities with `--cap-drop all` then add only needed ones
- Use `USER` instruction to switch from root
- Regularly scan images for vulnerabilities (`docker scan` or Trivy)
- Use content-trust (`DOCKER_CONTENT_TRUST=1`) to verify image signatures
- Limit resource usage with `--memory`, `--cpus` flags
- Use separate networks for frontend and backend services
- Enable Docker Bench Security for compliance checks

## Common Mistakes

- **Using `:latest` tag**: The latest tag is mutable and can break builds. Always pin to specific versions or digests.
- **Running as root inside container**: Containers running as root have elevated privileges on the host. Always create and use a non-root user.
- **Big final image size**: Including build tools, dependencies, and temporary files in the final image wastes disk and bandwidth. Use multi-stage builds.
- **Too many layers**: Each RUN, COPY, and ADD instruction creates a layer. Combine commands with `&&` and clean up in the same layer.
- **Ignoring `.dockerignore`**: Sending the entire project directory as build context slows builds. Add node_modules, .git, and build artifacts to `.dockerignore`.
- **Storing secrets in images**: Environment variables and files in images can be extracted by anyone with access to the image. Use secrets management.
- **Not setting restart policies**: Without restart policies, containers stop on failure. Use `restart: unless-stopped` for production.
- **Overusing bind mounts in production**: Bind mounts tie containers to host filesystem structure. Use named volumes for production data persistence.
- **Missing health checks**: Without health checks, orchestration platforms cannot determine if containers are actually running correctly.
- **Not handling signals correctly**: Node.js and other runtimes may not handle SIGTERM properly without an init process. Use tini or dumb-init.

## Libraries

### Official Docker Tools

| Tool | Purpose |
|------|---------|
| Docker Engine | Core container runtime |
| Docker Compose | Multi-container orchestration |
| Docker Swarm | Native clustering and orchestration |
| Docker Desktop | GUI for macOS/Windows development |
| Docker Hub | Public image registry |
| Docker Scout | Security and dependency analysis |
| Docker BuildKit | Enhanced build engine |
| Docker Scan | Vulnerability scanning |

### Complementary Tools

| Tool | Purpose |
|------|---------|
| Dive | Docker image layer analysis |
| Hadolint | Dockerfile linter |
| Trivy | Vulnerability scanner for containers |
| Grype | Vulnerability scanner |
| Buildah | Build OCI images without Docker daemon |
| Podman | Daemonless container engine |
| Kaniko | Build images in Kubernetes |
| SlimToolkit | Optimize container images |
| Watchtower | Automatic container updates |
| Portainer | Web UI for container management |

## Design Principles

### Immutable Infrastructure

Containers should be treated as immutable: once built, they should not be modified. Configuration changes should require building a new image, not modifying a running container. This ensures consistency across environments and enables reliable rollbacks.

### Single Concern per Container

Each container should run a single process or closely related set of processes. Avoid running multiple services (e.g., app server and database) in the same container. This enables independent scaling, lifecycle management, and failure isolation.

### Ephemeral by Design

Containers should be disposable. Any data that must persist beyond the container lifecycle belongs in volumes. Stateful configuration should be injected through environment variables or mounted configuration files, not embedded in the image.

### Defense in Depth

Security should be applied at multiple layers: image scanning, non-root user, read-only filesystem, capability dropping, network segmentation, and secrets management. No single security measure is sufficient; layers provide defense in depth.

## Coding Standards

### Dockerfile Organization

```dockerfile
# 1. FROM (base images)
FROM node:20-alpine AS builder

# 2. LABEL (metadata)
LABEL maintainer="..."

# 3. ARG/ENV (configuration)
ARG BUILD_ENV=production
ENV NODE_ENV=${BUILD_ENV}

# 4. RUN (system setup, in order)
RUN apk add --no-cache curl

# 5. WORKDIR
WORKDIR /app

# 6. COPY (dependency files first)
COPY package*.json ./
COPY tsconfig*.json ./

# 7. RUN (dependency installation)
RUN npm ci

# 8. COPY (application code)
COPY . .

# 9. RUN (build)
RUN npm run build

# 10. USER (security)
USER appuser

# 11. EXPOSE (ports)
EXPOSE 3000

# 12. HEALTHCHECK
HEALTHCHECK ...

# 13. ENTRYPOINT/CMD
CMD ["node", "server.js"]
```

### Naming Conventions

- Images: `registry/project/service:tag` (e.g., `ghcr.io/myorg/api:v1.2.3`)
- Containers: `project_service` (e.g., `myapp_postgres`)
- Compose services: descriptive names (e.g., `api-gateway`, `user-service`)
- Volumes: `project_data_type` (e.g., `myapp_postgres_data`)
- Networks: `tier` or `function` (e.g., `frontend`, `backend`, `monitoring`)
- Dockerfiles: `Dockerfile` for production, `Dockerfile.dev` for development

### Compose File Structure

```yaml
# 1. Version at top
version: '3.8'

# 2. Extensions (x- prefixes) for shared config
x-logging: &logging
  driver: json-file

# 3. Services section
services:
  service_name:
    # 3a. Image or build
    image: org/service:tag
    # 3b. Build context if building
    build:
      context: .
      dockerfile: Dockerfile
    # 3c. Runtime config
    ports: [...]
    environment: {...}
    volumes: [...]
    # 3d. Dependencies and health
    depends_on: {...}
    healthcheck: {...}
    # 3e. Resource constraints
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

# 4. Volumes
volumes:
  data_volume:

# 5. Networks
networks:
  app_network:
```
