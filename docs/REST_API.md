# ARES REST API

## Endpoints

### Version

**GET /version**

Returns API and application version information.

Response: `VersionResponse`

```json
{
    "version": "0.2.0",
    "api_version": "1.0.0",
    "python_version": "3.12.3",
    "platform": "Linux-6.8.0-x86_64",
    "request_id": "uuid"
}
```

### Health

**GET /health**

Returns system health status with component checks.

Response: `HealthResponse`

```json
{
    "status": "healthy",
    "version": "0.2.0",
    "uptime_seconds": 3600.0,
    "components": {
        "app": "healthy",
        "torch": "healthy",
        "cuda": "available"
    },
    "checks": {"python": "pass", "dependencies": "pass"},
    "request_id": "uuid"
}
```

### Predict

**POST /predict**

Make a single duplicate question prediction.

Request body: `PredictionRequest`

```json
{
    "question1": "What is Python?",
    "question2": "What is Python programming language?",
    "model": "Week 4 Improved DistilBERT",
    "threshold": 0.5,
    "reflect": true
}
```

Response: `PredictionResponse`

```json
{
    "question1": "What is Python?",
    "question2": "What is Python programming language?",
    "predicted_label": 1,
    "prediction": "duplicate",
    "prob_duplicate": 0.98,
    "prob_non_duplicate": 0.02,
    "confidence": 0.98,
    "threshold": 0.5,
    "model_label": "Improved DistilBERT (Week 4)",
    "latency_ms": 45.2,
    "trust_score": 0.95,
    "trust_level": "high",
    "risk_level": "low",
    "request_id": "uuid"
}
```

### Predict Batch

**POST /predict/batch**

Predict multiple question pairs.

Request body: `BatchPredictionRequest`

```json
{
    "pairs": [
        ["q1a", "q2a"],
        ["q1b", "q2b"]
    ],
    "model": "Week 4 Improved DistilBERT",
    "threshold": 0.5
}
```

### Predict Stream

**POST /predict/stream**

Server-Sent Events stream of predictions for multiple pairs.

Request body: `BatchPredictionRequest`

Response: SSE stream with `start`, `result`, `error`, `done` events.

### Predict Upload

**POST /predict/upload**

Upload a CSV file with question pairs for batch prediction.

Form data: `file` (CSV with two columns)

### Pipeline

**POST /pipeline**

Execute the full cognitive pipeline for a question pair.

### Reason

**POST /reason**

Execute the reasoning engine with detailed trace and evidence.

### Reflection

**POST /reflection**

Run trust scoring and confidence auditing on a prediction.

### Memory

**GET /memory**

List memory entries.

**POST /memory/search**

Search memory entries by query.

**GET /memory/stats**

Get memory statistics.

**POST /memory/clean**

Consolidate and clean memory.

### Plugins

**GET /plugins**

List installed plugins.

**GET /plugins/{id}**

Get plugin details.

**POST /plugins/{id}/enable**

Enable a plugin (admin only).

**POST /plugins/{id}/disable**

Disable a plugin (admin only).

**DELETE /plugins/{id}**

Uninstall a plugin (admin only).

### Benchmark

**GET /benchmark**

List available benchmark results.

**POST /benchmark/run**

Run a new benchmark.

### Config

**GET /config**

View configuration. Supports `?section=app` and `?verbose=true`.

**POST /config/validate**

Validate configuration files.

### Metrics

**GET /metrics**

Prometheus-format metrics.

**GET /metrics/json**

Metrics in JSON format.

### Trace

**POST /trace**

Run a decision trace for a question pair.

### Profile

**POST /profile**

Run the performance profiler.

**GET /profile/metrics**

Get profiler metrics.

### System

**GET /system/info**

Get comprehensive system information.
