# ARES Deployment Guide

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)
- NVIDIA GPU with CUDA (optional, for GPU-accelerated inference)

## Quick Start

### Local Development

```bash
# Install
pip install -e ".[dev]"

# Start API server
ares-serve

# The API is now available at http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Docker

```bash
# Build and start
docker compose up -d

# Check health
curl http://localhost:8000/api/v1/health

# View logs
docker compose logs -f ares-api
```

## Configuration

All configuration is via environment variables with the `ARES_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| ARES_HOST | 0.0.0.0 | API server host |
| ARES_PORT | 8000 | API server port |
| ARES_WORKERS | 4 | Number of uvicorn workers |
| ARES_LOG_LEVEL | info | Logging level |
| ARES_SECRET_KEY | (required) | JWT signing secret |
| ARES_JWT_ALGORITHM | HS256 | JWT algorithm |
| ARES_RATE_LIMIT_ENABLED | true | Enable rate limiting |
| ARES_RATE_LIMIT_REQUESTS | 100 | Max requests per window |
| ARES_CORS_ORIGINS | ["*"] | Allowed CORS origins |
| ARES_GRPC_PORT | 50051 | gRPC server port |
| ARES_OTEL_ENDPOINT | (empty) | OpenTelemetry endpoint |
| ARES_PROMETHEUS_ENABLED | true | Enable Prometheus metrics |

## Production Deployment

### Docker Compose (Production)

```bash
# Set secrets
export ARES_SECRET_KEY=$(openssl rand -hex 32)

# Start with monitoring
docker compose --profile monitoring up -d

# Access
# API: http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Kubernetes (Example)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ares-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ares-api
  template:
    metadata:
      labels:
        app: ares-api
    spec:
      containers:
      - name: ares-api
        image: ares-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ARES_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ares-secrets
              key: secret-key
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
        resources:
          limits:
            cpu: "4"
            memory: 8Gi
```

## Monitoring

### Prometheus Metrics

Available at `GET /api/v1/metrics` in Prometheus text format.

### Grafana

Import the ARES dashboard template to visualize:
- Request rates and latencies
- Model inference times
- Cache hit rates
- Error rates
- System resource usage
