# ARES gRPC API

The ARES gRPC API provides high-performance access to the same services
available through the REST API, using a JSON-over-HTTP protocol.

## Server

Default address: `localhost:50051`

The gRPC server implements a JSON-based protocol where each RPC method
maps to an HTTP POST endpoint.

## Methods

| Method | HTTP Path | Description |
|--------|-----------|-------------|
| Predict | POST /predict | Single prediction |
| PredictBatch | POST /predict_batch | Batch prediction |
| Health | GET /health | Health check |
| Version | GET /version | Version info |
| SystemInfo | POST /system_info | System information |
| RunPipeline | POST /pipeline | Pipeline execution |
| RunReflection | POST /reflection | Trust scoring |
| SearchMemory | POST /memory_search | Memory search |
| ListPlugins | POST /plugins | Plugin listing |

## Client Usage

```python
from ares.grpc.client import GrpcClient

client = GrpcClient("localhost", 50051)

# Health check
health = client.health()
print(health["status"])

# Make a prediction
result = client.predict(
    question1="What is Python?",
    question2="What is Python programming language?",
)
print(result["prediction"])
```
