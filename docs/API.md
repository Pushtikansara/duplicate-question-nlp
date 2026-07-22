# ARES API Reference

ARES (Advanced Reasoning Engine for Semantic Understanding) provides a
production-grade REST API, gRPC service, and Python SDK client for
semantic duplicate question detection and cognitive pipeline execution.

## Architecture

```
                    ┌──────────────────────┐
                    │    External Clients   │
                    │  (SDK, curl, apps)    │
                    └──────┬───────────────┘
                           │
              ┌────────────┼────────────┬───┘
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ REST API │ │ gRPC API │ │ Python   │
       │ :8000    │ │ :50051   │ │ SDK      │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │            │            │
            ▼            ▼            ▼
       ┌─────────────────────────────────────┐
       │         FastAPI Application          │
       │  Middleware → Auth → Rate Limit →   │
       │  Routers → Services                  │
       └────────────────┬────────────────────┘
                        │
                        ▼
       ┌─────────────────────────────────────┐
       │       ARES Engine (ares._engine)     │
       │  Predict → Reason → Reflect →      │
       │  Pipeline → Memory → Plugins       │
       └─────────────────────────────────────┘
```

## API Base URL

Production: `https://ares.example.com/api/v1`
Development: `http://localhost:8000/api/v1`

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## Authentication

ARES supports two authentication methods:

1. **JWT Bearer Tokens** — Short-lived access tokens (default 30 min) with
   refresh token support (default 7 days). Include in `Authorization: Bearer
   <token>` header.

2. **API Keys** — Long-lived keys for service-to-service communication.
   Include in `X-API-Key: <key>` header.

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all endpoints including system, config, plugins |
| `user` | Access to prediction, pipeline, memory, reflection endpoints |
| `reader` | Read-only access to health and version endpoints |

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Rate Limiting

Default: 100 requests per 60-second window per client IP with burst of 20.

## Response Format

All endpoints return JSON with consistent structure:

```json
{
    "field1": "value",
    "field2": 123,
    ...
    "request_id": "uuid",
    "timestamp": "2026-01-01T00:00:00"
}
```

Errors follow this format:

```json
{
    "detail": "Error description",
    "error_code": "ERROR_CODE",
    "status_code": 400,
    "request_id": "uuid",
    "timestamp": "2026-01-01T00:00:00"
}
```
