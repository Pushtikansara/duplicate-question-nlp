from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    READER = "reader"


class TokenData(BaseModel):
    sub: str
    role: UserRole = UserRole.USER
    permissions: list[str] = Field(default_factory=list)
    type: str = "access"


T = TypeVar("T")


class PredictionRequest(BaseModel):
    question1: str = Field(..., min_length=1, max_length=1000)
    question2: str = Field(..., min_length=1, max_length=1000)
    model: str | None = None
    threshold: float | None = Field(None, ge=0.0, le=1.0)
    reflect: bool | None = None


class PredictionResponse(BaseModel):
    question1: str = ""
    question2: str = ""
    predicted_label: int = 0
    prediction: str = "unknown"
    prob_duplicate: float = 0.0
    prob_non_duplicate: float = 0.0
    confidence: float = 0.0
    threshold: float = 0.5
    model_label: str = ""
    latency_ms: float = 0.0
    trust_score: float | None = None
    trust_level: str | None = None
    risk_level: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class BatchPredictionRequest(BaseModel):
    pairs: list[tuple[str, str]] = Field(..., min_length=1, max_length=1000)
    model: str | None = None
    threshold: float | None = None
    reflect: bool | None = None


class BatchPredictionResponse(BaseModel):
    results: list[PredictionResponse] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    average_latency_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class PipelineRequest(BaseModel):
    question1: str = Field(..., min_length=1, max_length=1000)
    question2: str = Field(..., min_length=1, max_length=1000)
    enable_perception: bool = True
    enable_routing: bool = True
    enable_memory: bool = True
    enable_semantic: bool = True
    enable_reasoning: bool = True
    enable_debate: bool = True
    enable_reflection: bool = True


class PipelineResponse(BaseModel):
    success: bool = False
    question1: str = ""
    question2: str = ""
    prediction: dict[str, Any] | None = None
    modules_executed: list[str] = Field(default_factory=list)
    modules_skipped: list[str] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    module_latencies: dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0
    trust_score: float | None = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class ReasonRequest(BaseModel):
    question1: str = Field(..., min_length=1, max_length=1000)
    question2: str = Field(..., min_length=1, max_length=1000)
    model: str | None = None
    threshold: float | None = None
    detailed: bool = False


class ReasonResponse(BaseModel):
    question1: str = ""
    question2: str = ""
    prediction: dict[str, Any] = Field(default_factory=dict)
    reasoning_trace: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class MemoryQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    memory_type: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryEntry(BaseModel):
    id: str = ""
    type: str = "unknown"
    content: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    tags: list[str] = Field(default_factory=list)


class ReflectionRequest(BaseModel):
    question1: str = Field(..., min_length=1, max_length=1000)
    question2: str = Field(..., min_length=1, max_length=1000)
    prediction: dict[str, Any] | None = None
    detailed: bool = False


class ReflectionResponse(BaseModel):
    trust_score: float = 0.0
    trust_level: str = "unknown"
    risk_level: str = "unknown"
    confidence: float = 0.0
    explanation: str = ""
    confidence_audit: dict[str, Any] | None = None
    consistency_check: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class BenchmarkRequest(BaseModel):
    name: str | None = None
    config: str = "default"
    epochs: int = Field(default=1, ge=1, le=10)
    model: str | None = None
    output: str | None = None


class BenchmarkResult(BaseModel):
    name: str = ""
    status: str = "completed"
    metrics: dict[str, float] = Field(default_factory=dict)
    config: str = "default"
    model: str = "default"
    epochs: int = 1
    total_latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class ConfigResponse(BaseModel):
    sections: dict[str, Any] = Field(default_factory=dict)
    source: str = "yaml"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class MetricsResponse(BaseModel):
    metrics: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class TraceRequest(BaseModel):
    question1: str = Field(..., min_length=1, max_length=1000)
    question2: str = Field(..., min_length=1, max_length=1000)
    model: str | None = None
    threshold: float | None = None
    include_decision: bool = True


class TraceResponse(BaseModel):
    trace: dict[str, Any] = Field(default_factory=dict)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class ProfileRequest(BaseModel):
    duration_seconds: int = Field(default=10, ge=1, le=300)
    include_memory: bool = True
    include_cpu: bool = True


class ProfileResponse(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    functions: list[dict[str, Any]] = Field(default_factory=list)
    total_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class HealthResponse(BaseModel):
    status: str = "unknown"
    version: str = ""
    uptime_seconds: float = 0.0
    components: dict[str, str] = Field(default_factory=dict)
    checks: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class SystemInfoResponse(BaseModel):
    version: str = ""
    python_version: str = ""
    platform: str = ""
    cpu_cores: int = 0
    memory_gb: float = 0.0
    gpu_available: bool = False
    gpu_name: str | None = None
    cuda_version: str | None = None
    torch_version: str = ""
    dependencies: dict[str, str] = Field(default_factory=dict)
    config_file_count: int = 0
    model_available: bool = False
    plugins_loaded: int = 0
    uptime_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class VersionResponse(BaseModel):
    version: str = ""
    python_version: str = ""
    platform: str = ""
    api_version: str = "1.0.0"
    build: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class ErrorResponse(BaseModel):
    detail: str = ""
    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""
    errors: list[dict[str, Any]] | None = None
